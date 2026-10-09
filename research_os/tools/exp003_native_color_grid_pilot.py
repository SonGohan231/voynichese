#!/usr/bin/env python3
"""EXP003 source-native exploratory color/layout audit on three source-matched canvases.

Does not infer color semantics or flow, or claim statistical significance.
"""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

from exp003_yale_visual_inventory import fetch_image, classify_pixel_masks, resize_photo

ROOT=Path(__file__).resolve().parents[1]
EXP2=ROOT/"experiments"/"EXP-2026-002"
EXP3=ROOT/"experiments"/"EXP-2026-003"
SOURCE=EXP2/"yale_archived_jpeg_provenance_crosswalk_2026-10-09.json"
OUTPUT=EXP3/"native_color_grid_pilot_2026-10-09.json"
FOLIOS=["9r","85v and 86r (foldout)","94v and 95r"]


def region_grid(bgr, masks):
    h,w=bgr.shape[:2]
    gray=cv2.cvtColor(bgr,cv2.COLOR_BGR2GRAY)
    edges=cv2.Canny(cv2.GaussianBlur(gray,(3,3),0),65,130) > 0
    rows=[]
    for yi in range(3):
        for xi in range(3):
            y0,y1=round(yi*h/3),round((yi+1)*h/3)
            x0,x1=round(xi*w/3),round((xi+1)*w/3)
            region=(slice(y0,y1),slice(x0,x1))
            area=(y1-y0)*(x1-x0)
            counts={k:int(np.count_nonzero(v[region])) for k,v in masks.items()}
            rows.append({
                "grid_row":yi,"grid_col":xi,
                "normalized_bbox_xywh":[round(xi/3,5),round(yi/3,5),round(1/3,5),round(1/3,5)],
                "pixel_count":int(area),"perceived_color_pixel_counts":counts,
                "perceived_color_region_fractions":{k:round(v/area,6) for k,v in counts.items()},
                "grayscale_canny_edge_fraction":round(float(np.mean(edges[region])),6),
            })
    return rows


def audit(crosswalk,out):
    d=json.loads(Path(crosswalk).read_text(encoding="utf-8"))
    entries={}
    for e in d["archive_files"]:
        if e["yale_label"] in FOLIOS:
            if e["yale_label"] in entries:
                raise ValueError("Duplicate requested Yale label")
            entries[e["yale_label"]]=e
    if set(entries)!=set(FOLIOS):
        raise ValueError("Requested folio source missing from archival provenance crosswalk")
    results=[]
    for label in FOLIOS:
        entry=entries[label]
        original=fetch_image(entry)  # independent SHA256 verification inside fetch_image
        native_h,native_w=original.shape[:2]
        working=resize_photo(original)
        mask, paper=classify_pixel_masks(working)  # conservative color appearance only
        color_totals={k:int(np.count_nonzero(v)) for k,v in mask.items()}
        results.append({
          "canvas_oid":entry["canvas_oid"],"original_label":label,
          "archived_jpeg_source_path":entry["path"],
          "verified_sha256":entry["imported_reported_sha256"],
          "original_width_height_px":[int(native_w),int(native_h)],
          "working_width_height_px":[int(working.shape[1]),int(working.shape[0])],
          "paper_reference":paper,
          "color_pixel_counts":color_totals,
          "color_image_fractions":{k:round(v/mask[k].size,6) for k,v in color_totals.items()},
          "grid":region_grid(working,mask),
          "interpretation":"DIGITAL_COLOR_LAYOUT_ONLY_NOT_SEMANTIC_OBJECT_ANNOTATION",
        })
        print("AUDITED",label,entry["canvas_oid"],color_totals,flush=True)
    report={
       "schema":"voynich-exp003-source-native-grid-v1",
       "science_status":"EXPLORATORY_NO_STATISTICAL_TEST",
       "cv_status":"SOURCE_SHA256_VERIFIED_AND_PIXEL_GRID_COMPUTED",
       "external_manuscript_identification":"CANDIDATE_ONLY",
       "source_archive_hash_table_sha256":hashlib.sha256(Path(crosswalk).read_bytes()).hexdigest(),
       "units":"three separate archived digital photograph canvases, not necessarily 3 codicologically independent leaves",
       "negative_controls_status":"NOT_EXECUTED; prior to inference, freeze parchment/background and ordinary iconography nulls",
       "color": "digital color mask appearance HSV/OpenCV Lab; not chemical identification nor calibrated Lab",
       "graph_direction":"NOT_MEASURED",
       "perspective_or_depth":"NOT_MEASURED",
       "results":results,
    }
    out=Path(out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("WROTE",out,flush=True)
    return report


def selftest():
    bgr=np.full((120,150,3),240,dtype=np.uint8)
    m={"a":np.zeros((120,150),dtype=bool),"b":np.zeros((120,150),dtype=bool)}
    m["a"][:40,:50]=True
    r=region_grid(bgr,m)
    assert len(r)==9
    assert sum(x["perceived_color_pixel_counts"]["a"] for x in r)==2000
    assert abs(r[0]["perceived_color_region_fractions"]["a"]-1)<1e-9
    assert all(0<=x["grayscale_canny_edge_fraction"]<=1 for x in r)
    print("SELFTEST PASS: full 3x3 partition, non-overlap and fraction denominator")


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--crosswalk",default=str(SOURCE))
    ap.add_argument("--output",default=str(OUTPUT))
    ap.add_argument("--selftest",action="store_true")
    args=ap.parse_args()
    selftest() if args.selftest else audit(args.crosswalk,args.output)
