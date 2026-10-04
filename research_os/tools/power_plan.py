#!/usr/bin/env python3
"""Pre-data cluster power planning for the EXP-2026-001 held-out test."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import NormalDist
from typing import Any

from readiness import group_keys, load_records


def build_power_plan(
    records_dir: Path,
    alpha: float = 0.01,
    target_power: float = 0.80,
    held_out_fraction: float = 0.20,
    target_standardized_effect: float = 0.75,
) -> dict[str, Any]:
    if not 0 < alpha < 0.5 or not 0.5 < target_power < 1:
        raise ValueError("alpha and target_power outside supported range")
    if not 0 < held_out_fraction < 1 or target_standardized_effect <= 0:
        raise ValueError("invalid held-out fraction or target effect")
    records = load_records(records_dir)
    groups = group_keys(records)
    folio_records = [record for record in records if record["source"].get("logical_role") == "FOLIO"]
    folio_groups = sorted({groups[record["record_id"]] for record in folio_records})
    held_out_groups = round(len(folio_groups) * held_out_fraction)
    z_alpha = NormalDist().inv_cdf(1 - alpha)
    z_power = NormalDist().inv_cdf(target_power)
    required_groups = math.ceil(((z_alpha + z_power) / target_standardized_effect) ** 2)
    detectable_effect = (z_alpha + z_power) / math.sqrt(held_out_groups) if held_out_groups else None
    adequate = held_out_groups >= required_groups
    return {
        "schema_version": "1.0",
        "experiment_id": "EXP-2026-001",
        "status": "ADEQUATE_FOR_PREREGISTERED_LARGE_EFFECT" if adequate else "UNDERPOWERED",
        "method": "one-sided normal approximation on independent folio-group paired score differences",
        "assumptions": {
            "alpha": alpha,
            "target_power": target_power,
            "held_out_fraction": held_out_fraction,
            "target_standardized_effect": target_standardized_effect,
            "effect_definition": "mean held-out folio-group score advantage divided by SD of folio-group paired differences",
            "independent_unit": "connected manuscript leaf group",
        },
        "inventory": {
            "folio_records": len(folio_records),
            "independent_folio_groups": len(folio_groups),
            "planned_held_out_groups": held_out_groups,
        },
        "calculation": {
            "z_alpha": z_alpha,
            "z_power": z_power,
            "required_held_out_groups": required_groups,
            "minimum_detectable_standardized_effect_at_planned_n": detectable_effect,
        },
        "decision_policy": {
            "smaller_effect": "INCONCLUSIVE unless a separately preregistered exact power analysis supports it",
            "post_hoc_power": "FORBIDDEN",
            "record_level_pseudoreplication": "FORBIDDEN",
            "held_out_labels_used": False,
        },
        "limitations": [
            "Normal approximation is a planning calculation, not the final permutation test.",
            "Power can fall after stratification, exclusions, annotation failure, or missing groups.",
            "The calculation does not validate automated candidates or any Voynich hypothesis.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("records_dir", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--alpha", type=float, default=0.01)
    parser.add_argument("--power", type=float, default=0.80)
    parser.add_argument("--held-out-fraction", type=float, default=0.20)
    parser.add_argument("--target-effect", type=float, default=0.75)
    args = parser.parse_args()
    report = build_power_plan(
        args.records_dir, args.alpha, args.power, args.held_out_fraction, args.target_effect
    )
    rendered = json.dumps(report, indent=2) + "\n"
    if args.report:
        args.report.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["status"].startswith("ADEQUATE") else 2


if __name__ == "__main__":
    raise SystemExit(main())
