#!/usr/bin/env python3
"""EXP004 sensitivity follow-up: manually seeded *approximate* central blue motifs.

The Hough circle candidates are larger than the colored central shapes,
occasionally covering multiple neighbouring roundels. This separate pilot
uses four **unblinded manually visually located** centers/radii. NOT a
confirmed object segmentation; keep previous automated Hough run unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path
import cv2
from exp003_yale_visual_inventory import fetch_image
from exp004_blue_radial_components import candidate,blue_signature_score,make_board

ROOT=Path(__file__).resolve().parents[1]
EXP2=ROOT/"experiments"/"EXP-2026-002"
EXP4=ROOT/"experiments"/"EXP-2026-004"
CROSS=EXP2/"yale_archived_jpeg_provenance_crosswalk_2026-10-09.json"
# Chosen by unblinded qualitative inspection of six source overview images,
# not optimised using similarity scores and never usable as independent held-out.
SEEDS=[
  {"canvas_oid":"1006197","name":"f68v_blue_small_lobed","center":[.5578,.4414],"radius_short":.068},
  {"canvas_oid":"1006197","name":"f68v_blue_long_ray","center":[.8387,.4489],"radius_short":.162},
  {"canvas_oid":"1006231","name":"rosettes_upper_blue_ray","center":[.556,.1788],"radius_short":.080},
  {"canvas_oid":"1006231","name":"rosettes_lower_blue_ray","center":[.544,.799],"radius_short":.085},
]

def main(out,board):
    ledger=json.loads(CROSS.read_text(encoding="utf-8"))
    sources={str(x["canvas_oid"]):x for x in ledger["archive_files"]}
    images={}
    for oid in sorted({x["canvas_oid"] for x in SEEDS}):
        original=fetch_image(sources[oid])
        h,w=original.shape[:2]
        resize=min(1.,2100/max(w,h))
        im=cv2.resize(original,(round(w*resize),round(h*resize)),
                      interpolation=cv2.INTER_AREA) if resize<1 else original
        images[oid]=im
    features=[]
    for x in SEEDS:
        entry=sources[x["canvas_oid"]]
        bgr=images[x["canvas_oid"]]
        h,w=bgr.shape[:2]
        c=(x["center"][0]*w,x["center"][1]*h)
        r=x["radius_short"]*min(w,h)
        model=candidate(bgr,c,r)
        features.append({
           "candidate_id":x["name"],"canvas_oid":x["canvas_oid"],"folio":entry["yale_label"],
           "source_sha256":entry["imported_reported_sha256"],
           "center_xy_fraction":x["center"],"circle_radius_short_axis":x["radius_short"],
           "radius_origin":"ASSISTANT_UNBLINDED_EXPLORATORY_VISUAL_PICK",
           "physical_groups":entry["physical_group_ids"],**model
        })
    pairs=[]
    for f in features[:2]:
        for g in features[2:]:
            pairs.append({"a":f["candidate_id"],"b":g["candidate_id"],
                          "digital_blue_radial_score":blue_signature_score(f,g),
                          "median_digital_runs_a":f["median_blue_runs"],
                          "median_digital_runs_b":g["median_blue_runs"],
                          "both_blue_run_stable":bool(f["stable_enough_for_visual_review"] and
                            g["stable_enough_for_visual_review"]),
                          "same_object_or_3d_view":"NOT_TESTED_INDEPENDENTLY"})
    pairs.sort(key=lambda x:-x["digital_blue_radial_score"])
    report={
      "schema":"exp004-manually-seeded-color-radial-pilot-v1",
      "status":"EXPLORATORY_UNBLINDED_CANNOT_CONFIRM_OBJECT_IDENTITY",
      "source_crosswalk_sha256":hashlib.sha256(CROSS.read_bytes()).hexdigest(),
      "manual_roi_seeds":len(features),
      "between_folio_comparisons":len(pairs),
      "reference_algorithm":"exp004_blue_radial_components.py fixed 3x3 saturation/occupancy thresholds",
      "regions":features,"pairs":pairs,
      "limitations":[
        "Seed locations/radii from qualitative source image inspection are NOT blinded measurements",
        "Pixel ring-run counts != real sector/star/merlon counts",
        "No perspective estimation, relative anatomical landmark graphs or topology compared",
        "Updated radii are picked BEFORE rerun not via automated optimization but must be kept discovery-only",
        "Original high-resolution Yale source hashes checked, preview processed after 2100px resampling",
        "Two qualified independent annotators still needed for any historical identity"
      ]
    }
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    board=Path(board);board.parent.mkdir(parents=True,exist_ok=True)
    make_board(features,images,board)
    print("EXP004_CURATED_BLUE",len(features),"ROI",len(pairs),"CROSS_FOLIO_PAIRS",
          "STABLE",sum(int(x["both_blue_run_stable"]) for x in pairs),flush=True)
    for x in features:
        print("FEATURE",x["candidate_id"],x["median_blue_runs"],x["blue_runs_min_max"],
              x["stable_enough_for_visual_review"],flush=True)
    for x in pairs:print("PAIR",x["a"],x["b"],x["digital_blue_radial_score"],
                        x["both_blue_run_stable"],flush=True)

def selftest():
    assert len(SEEDS)==4
    assert len(set(x["candidate_id"] for x in SEEDS))==4
    assert all(0.03<x["radius_short"]<.25 for x in SEEDS)
    assert all(0<x["center"][0]<1 and 0<x["center"][1]<1 for x in SEEDS)
    print("EXP004_CURATED_SEED_SELFTEST_PASS nonoverlap IDs, plausible frame coordinates")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",default=str(EXP4/"manually_seeded_blue_radial_v1.json"))
    p.add_argument("--board",default=str(EXP4/"manually_seeded_blue_radial_board.png"))
    p.add_argument("--selftest",action="store_true")
    a=p.parse_args()
    if a.selftest:selftest()
    else:main(a.out,a.board)
