#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
EXP = Path(__file__).resolve().parent
MANIFEST_PATH = EXP / "FROZEN_MANIFEST.json"
OUTPUT = EXP / "generated"
DIRECTIONS = ("N", "E", "S", "W")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def extract_patch(image: np.ndarray, centre: tuple[int, int], size: int) -> np.ndarray:
    x, y = centre
    half = size // 2
    x1, y1 = x - half, y - half
    x2, y2 = x1 + size, y1 + size
    out = np.full((size, size, 3), 255, dtype=np.uint8)
    sx1, sy1 = max(0, x1), max(0, y1)
    sx2, sy2 = min(image.shape[1], x2), min(image.shape[0], y2)
    if sx2 <= sx1 or sy2 <= sy1:
        return out
    ox1, oy1 = sx1 - x1, sy1 - y1
    out[oy1:oy1 + (sy2 - sy1), ox1:ox1 + (sx2 - sx1)] = image[sy1:sy2, sx1:sx2]
    return out


def feature_vector(patch: np.ndarray) -> dict[str, float]:
    gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
    dark = gray < 150
    mask = dark.astype(np.uint8)
    count, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    areas = stats[1:, cv2.CC_STAT_AREA] if count > 1 else np.array([], dtype=float)
    largest = float(areas.max() / mask.size) if areas.size else 0.0
    components = float(np.sum(areas >= 3) / 100.0) if areas.size else 0.0
    edges = cv2.Canny(gray, 60, 140)
    blue = (
        (hsv[:, :, 0] >= 80)
        & (hsv[:, :, 0] <= 125)
        & (hsv[:, :, 1] >= 35)
        & (hsv[:, :, 2] < 220)
    )
    chroma = hsv[:, :, 1] >= 30
    hist = np.histogram(gray, bins=32, range=(0, 256))[0].astype(float)
    probabilities = hist / max(1.0, hist.sum())
    entropy = -float(np.sum(probabilities[probabilities > 0] * np.log2(probabilities[probabilities > 0]))) / 5.0
    lap_var = float(np.var(cv2.Laplacian(gray, cv2.CV_64F)) / 10000.0)
    return {
        "dark_ratio": float(dark.mean()),
        "edge_density": float((edges > 0).mean()),
        "blue_ratio": float(blue.mean()),
        "chroma_ratio": float(chroma.mean()),
        "entropy": entropy,
        "largest_component": largest,
        "component_count": components,
        "lap_var": lap_var,
    }


def score_pairings(features: dict[str, dict[str, float]], names: list[str], pairings: dict) -> dict[str, float]:
    matrix = np.array([[features[direction][name] for name in names] for direction in DIRECTIONS], dtype=float)
    deviation = matrix.std(axis=0)
    deviation[deviation < 1e-12] = 1.0
    standardized = (matrix - matrix.mean(axis=0)) / deviation
    by_direction = {direction: standardized[index] for index, direction in enumerate(DIRECTIONS)}
    result: dict[str, float] = {}
    for pairing_name, pairs in pairings.items():
        result[pairing_name] = float(sum(np.linalg.norm(by_direction[a] - by_direction[b]) for a, b in pairs))
    return result


def load_diagram(entry: dict, size_multiplier: float = 1.0, dx_fraction: float = 0.0, dy_fraction: float = 0.0) -> tuple[dict, dict]:
    source = ROOT / entry["source_path"]
    actual_sha = sha256(source)
    if actual_sha != entry["source_sha256"]:
        raise RuntimeError(f"SHA mismatch for {entry['id']}: {actual_sha}")
    original = cv2.imread(str(source), cv2.IMREAD_COLOR)
    if original is None:
        raise RuntimeError(f"Cannot read {source}")
    target_width, target_height = [int(v) for v in entry["analysis_grid_px"]]
    image = cv2.resize(original, (target_width, target_height), interpolation=cv2.INTER_AREA)
    base_crop = int(entry["crop_size_px"])
    crop_size = max(20, int(round(base_crop * size_multiplier)))
    feature_rows: dict[str, dict[str, float]] = {}
    patch_metadata: dict[str, dict] = {}
    for direction in DIRECTIONS:
        x, y = [int(v) for v in entry["sector_centres_px"][direction]]
        centre = (
            int(round(x + dx_fraction * base_crop)),
            int(round(y + dy_fraction * base_crop)),
        )
        patch = extract_patch(image, centre, crop_size)
        feature_rows[direction] = feature_vector(patch)
        patch_metadata[direction] = {"centre_px": list(centre), "crop_size_px": crop_size}
    return feature_rows, {
        "source_path": entry["source_path"],
        "source_sha256": actual_sha,
        "analysis_grid_px": [target_width, target_height],
        "patches": patch_metadata,
    }


def exact_p_value(heldout_scores: list[dict[str, float]], predicted: str) -> tuple[float, int, int, float]:
    names = list(heldout_scores[0])
    observed = float(sum(row[predicted] for row in heldout_scores))
    null_values = []
    for assignment in itertools.product(names, repeat=len(heldout_scores)):
        null_values.append(sum(heldout_scores[index][choice] for index, choice in enumerate(assignment)))
    count = int(sum(value <= observed + 1e-12 for value in null_values))
    p_value = (count + 1) / (len(null_values) + 1)
    return p_value, count, len(null_values), observed


def execute_configuration(manifest: dict, size_multiplier: float, dx_fraction: float, dy_fraction: float) -> dict:
    all_features: dict[str, dict] = {}
    provenance: dict[str, dict] = {}
    scores: dict[str, dict[str, float]] = {}
    for entry in manifest["diagrams"]:
        diagram_features, diagram_provenance = load_diagram(entry, size_multiplier, dx_fraction, dy_fraction)
        all_features[entry["id"]] = diagram_features
        provenance[entry["id"]] = diagram_provenance
        scores[entry["id"]] = score_pairings(diagram_features, manifest["feature_names"], manifest["pairings"])
    training_id = next(entry["id"] for entry in manifest["diagrams"] if entry["role"] == "TRAIN")
    heldout_ids = [entry["id"] for entry in manifest["diagrams"] if entry["role"] == "HELD_OUT"]
    predicted = min(scores[training_id], key=scores[training_id].get)
    preferences = {diagram_id: min(scores[diagram_id], key=scores[diagram_id].get) for diagram_id in heldout_ids}
    wins = sum(preference == predicted for preference in preferences.values())
    heldout_scores = [scores[diagram_id] for diagram_id in heldout_ids]
    p_value, tail_count, null_count, observed = exact_p_value(heldout_scores, predicted)
    numeric_status = "PASS" if wins >= 3 and p_value < 0.05 else "FAIL"
    return {
        "size_multiplier": size_multiplier,
        "dx_fraction": dx_fraction,
        "dy_fraction": dy_fraction,
        "training_pairing": predicted,
        "heldout_preferences": preferences,
        "heldout_wins": wins,
        "exact_permutation_p": p_value,
        "lower_or_equal_null_assignments": tail_count,
        "null_assignment_count": null_count,
        "observed_transfer_score": observed,
        "numeric_status": numeric_status,
        "features": all_features,
        "pairing_scores": scores,
        "provenance": provenance,
    }


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    primary = execute_configuration(manifest, 1.0, 0.0, 0.0)
    sensitivity = []
    for size_multiplier in manifest["sensitivity_grid"]["crop_size_multipliers"]:
        for dx_fraction, dy_fraction in manifest["sensitivity_grid"]["common_page_translations_in_base_crop_fraction"]:
            run = execute_configuration(manifest, float(size_multiplier), float(dx_fraction), float(dy_fraction))
            sensitivity.append({
                "size_multiplier": run["size_multiplier"],
                "dx_fraction": run["dx_fraction"],
                "dy_fraction": run["dy_fraction"],
                "training_pairing": run["training_pairing"],
                "heldout_wins": run["heldout_wins"],
                "exact_permutation_p": run["exact_permutation_p"],
                "numeric_status": run["numeric_status"],
            })
    training_stability = sum(row["training_pairing"] == primary["training_pairing"] for row in sensitivity) / len(sensitivity)
    sensitivity_pass_rate = sum(row["numeric_status"] == "PASS" for row in sensitivity) / len(sensitivity)
    result = {
        "experiment_id": manifest["experiment_id"],
        "scientific_status": manifest["scientific_status"],
        "primary": {key: value for key, value in primary.items() if key not in {"features", "pairing_scores", "provenance"}},
        "training_pairing_stability": training_stability,
        "sensitivity_numeric_pass_rate": sensitivity_pass_rate,
        "final_conclusion": (
            "PILOT_NUMERIC_PASS_NOT_CONFIRMATORY" if primary["numeric_status"] == "PASS" else "FAIL_NO_HELDOUT_TRANSFER_AT_95_PERCENT"
        ),
        "interpretation": (
            "The learned four-sector pairing transferred under the frozen numeric gate, but the post-inspection selection makes this a pilot only."
            if primary["numeric_status"] == "PASS"
            else "The frozen pairing did not beat the exact permutation null at p < 0.05 and must not be used as evidence for a shared allegorical opposition system."
        ),
        "source_policy": "Official Yale JPEG files were SHA-verified, resized only in memory, and never modified.",
    }
    write_json(OUTPUT / "RESULT.json", result)
    feature_rows = []
    for diagram_id, directions in primary["features"].items():
        for direction, values in directions.items():
            feature_rows.append({"diagram_id": diagram_id, "direction": direction, **values})
    write_csv(OUTPUT / "SECTOR_FEATURES.csv", feature_rows, ["diagram_id", "direction", *manifest["feature_names"]])
    pairing_rows = []
    for diagram_id, values in primary["pairing_scores"].items():
        preference = min(values, key=values.get)
        for pairing_name, score in values.items():
            pairing_rows.append({
                "diagram_id": diagram_id,
                "pairing": pairing_name,
                "score": score,
                "is_preferred": pairing_name == preference,
                "is_training_prediction": pairing_name == primary["training_pairing"],
            })
    write_csv(OUTPUT / "PAIRING_SCORES.csv", pairing_rows, ["diagram_id", "pairing", "score", "is_preferred", "is_training_prediction"])
    write_csv(
        OUTPUT / "SENSITIVITY.csv",
        sensitivity,
        ["size_multiplier", "dx_fraction", "dy_fraction", "training_pairing", "heldout_wins", "exact_permutation_p", "numeric_status"],
    )
    write_json(OUTPUT / "PROVENANCE.json", primary["provenance"])
    report = f"""# {manifest['experiment_id']} — wynik\n\n"
    report += f"- Status naukowy: `{manifest['scientific_status']}`\n"
    report += f"- Para wybrana na f57v: `{primary['training_pairing']}`\n"
    report += f"- Zgodne diagramy held-out: `{primary['heldout_wins']}/4`\n"
    report += f"- Dokładne p permutacyjne: `{primary['exact_permutation_p']:.6f}`\n"
    report += f"- Bramka liczbowa: `{primary['numeric_status']}`\n"
    report += f"- Wniosek końcowy: `{result['final_conclusion']}`\n"
    report += f"- Stabilność pary treningowej w siatce czułości: `{training_stability:.3f}`\n"
    report += f"- Odsetek PASS w siatce czułości: `{sensitivity_pass_rate:.3f}`\n\n"
    report += "## Preferencje held-out\n\n"
    for diagram_id, preference in primary["heldout_preferences"].items():
        report += f"- `{diagram_id}`: `{preference}`\n"
    report += "\n## Interpretacja\n\n" + result["interpretation"] + "\n"
    (OUTPUT / "REPORT.md").write_text(report, encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if primary["numeric_status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
