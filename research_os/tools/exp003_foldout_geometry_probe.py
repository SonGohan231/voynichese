#!/usr/bin/env python3
"""EXP-2026-003: geometry-only exploratory measurements on 8 foldout images.

This tool processes REAL verified Yale JPEG pixels at a 1800px working scale.
It proposes circular contours, long-line candidates and image-plane edge
densities. No circle equals a proven rosette; no straight line equals a
historical fold; no image-plane layout equals real 3D depth.

Scientific admissibility gate: independent native-resolution human examination.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys

import cv2
import numpy as np

from exp003_yale_visual_inventory import fetch_image, EXPERIMENT, ROOT

PRIORITY_OIDS = (
    "1006194", "1006195", "1006196", "1006197", "1006228",
    "1006229", "1006230", "1006231",
)
SOURCE = EXPERIMENT / "yale_archived_jpeg_provenance_crosswalk_2026-10-09.json"

def normalized(n, length):
    return round(max(0., min(1., float(n) / length)), 6)

def image_crop_url(oid, bbox):
    x,y,w,h = bbox
    left=max(0.,x*100-1.1); top=max(0.,y*100-1.1)
    dx=min(100.-left,w*100+2.2); dy=min(100.-top,h*100+2.2)
    box=",".join(str(round(q,3)) for q in (left,top,dx,dy))
    return f"https://collections.library.yale.edu/iiif/2/{oid}/pct:{box}/!1100,1100/0/default.jpg"

def derive_geometry(original,oid):
    source_h,source_w = original.shape[:2]
    max_side=max(source_w,source_h)
    scale=min(1.,1800/max_side)
    if scale<1:
        im=cv2.resize(original,(round(source_w*scale),round(source_h*scale)),
                      interpolation=cv2.INTER_AREA)
    else:
        im=original
    height,width=im.shape[:2]
    gray=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    smooth=cv2.medianBlur(gray,5)
    edge=cv2.Canny(smooth,45,135,L2gradient=True)
    shorter=min(width,height)
    # We search deliberately broad size ranges; very small diagram rings are
    # not reliably captured and no detection is automatically a valid object.
    circles=cv2.HoughCircles(smooth,cv2.HOUGH_GRADIENT,dp=1.6,
                            minDist=max(60,int(shorter*.185)),
                            param1=105,param2=35,
                            minRadius=max(25,int(shorter*.055)),
                            maxRadius=max(50,int(shorter*.285)))
    possible=[]
    if circles is not None:
        for c in circles[0]:
            x,y,rad=(float(v) for v in c)
            box=[normalized(max(0.,x-rad),width),
                 normalized(max(0.,y-rad),height),
                 normalized(min(width,x+rad)-max(0,x-rad),width),
                 normalized(min(height,y+rad)-max(0,y-rad),height)]
            possible.append({"center_xy":[normalized(x,width),normalized(y,height)],
                             "radius_fraction_of_minimum_axis":round(rad/shorter,6),
                             "box_xywh":box,
                             "crop_url":image_crop_url(oid,box),
                             "label":"ROUND_SHAPE_CANDIDATE_UNKNOWN",
                             "human_verified":False})
    possible.sort(key=lambda x:(x["center_xy"][1],x["center_xy"][0]))
    possible=possible[:32]
    lines=cv2.HoughLinesP(edge,1,np.pi/180,threshold=max(80,int(shorter*.06)),
                           minLineLength=max(100,int(shorter*.16)),
                           maxLineGap=max(16,int(shorter*.021)))
    line_candidates=[]
    if lines is not None:
        for arr in lines[:,0]:
            x1,y1,x2,y2=(int(v) for v in arr)
            delta_x=x2-x1;delta_y=y2-y1
            span=math.hypot(delta_x,delta_y)
            ang=(math.degrees(math.atan2(delta_y,delta_x))+180)%180
            if (min(ang,180-ang)>12 and abs(ang-90)>12):
                continue
            line_candidates.append({
                "start_xy":[normalized(x1,width),normalized(y1,height)],
                "end_xy":[normalized(x2,width),normalized(y2,height)],
                "angle_deg_mod_180":round(ang,2),
                "length_fraction_of_long_axis":round(span/max(width,height),6),
                "label":"STRAIGHT_IMAGE_LINE_NOT_FOLD_PROOF",
                "human_verified":False})
    line_candidates.sort(key=lambda x:-x["length_fraction_of_long_axis"])
    line_candidates=line_candidates[:24]
    nx,ny=(3,3) if oid=="1006231" else ((3,1) if width>1.65*height else (2,2))
    sectors=[]
    for ry in range(ny):
        for cx in range(nx):
            x0=round(width*cx/nx);x1=round(width*(cx+1)/nx)
            y0=round(height*ry/ny);y1=round(height*(ry+1)/ny)
            crop=edge[y0:y1,x0:x1]
            sectors.append({"row":ry+1,"column":cx+1,
                            "box_xywh":[round(cx/nx,6),round(ry/ny,6),
                                        round(1/nx,6),round(1/ny,6)],
                            "edge_pixel_fraction":round(float(np.count_nonzero(crop)/crop.size),6),
                            "semantic_role":"UNKNOWN_UNVERIFIED_GRID_TILE"})
    return {
        "canvas_oid":oid,"native_size_pixels":[source_w,source_h],
        "working_size_pixels":[width,height],
        "circles_algorithm":"OpenCV HoughCircles after grayscale median filter",
        "line_algorithm":"OpenCV Canny + HoughLinesP; near horizontal/vertical orientations",
        "candidate_circular_regions":possible,
        "straight_image_line_candidates":line_candidates,
        "grid_tile_edge_density":sectors,
        "total_detected_circular_candidates":len(possible),
        "total_straight_line_candidates":len(line_candidates),
        "confirmed_rosettes":0,
        "confirmed_towers":0,
        "confirmed_physical_fold_axes":0,
        "historical_2point5d_depth":"NOT_MEASURED"
    }

def main(output):
    inventory=json.loads(SOURCE.read_text(encoding="utf-8"))
    source={x["canvas_oid"]:x for x in inventory["archive_files"]}
    evidence=[]
    failures=[]
    for oid in PRIORITY_OIDS:
        f=source.get(oid)
        if not f: raise RuntimeError(f"Missing image source for {oid}")
        try:
            raw=fetch_image(f)  # per-photo SHA-256 rechecked on source JPEG bytes
            report=derive_geometry(raw,oid)
            del raw
            report["source_path"]=f["path"]
            report["source_sha256_verified"]=f["imported_reported_sha256"]
            report["yale_original_label"]=f["yale_label"]
            evidence.append(report)
            print(f"[{len(evidence)}/8] {oid}: circle-candidates={report['total_detected_circular_candidates']}, long-lines={report['total_straight_line_candidates']}",flush=True)
        except Exception as exc:
            failures.append({"canvas_oid":oid,"source_path":f["path"],"error":str(exc)})
            print(f"FAILED {oid}: {exc}",flush=True)
    result={
        "schema":"exp-2026-003/foldout-geometry-exploratory-v1",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "status":"IMAGE_GEOMETRY_EXPLORATORY_NO_PHYSICAL_VERIFICATION" if not failures else "PARTIAL_SOURCE_FAILURE",
        "images_expected":8,"images_successful":len(evidence),"images_failed":len(failures),
        "sources":evidence,"failures":failures,
        "physical_fold_hypotheses":"UNKNOWN_AND_NOT_TESTED_AGAINST_A_CONSERVATOR",
        "perspective":"IMAGE_PLANE_MEASUREMENTS_ONLY",
        "science_status":"INCONCLUSIVE_NOT_RUN",
        "annotations_human_verified":0,
        "red_flags":[
            "A circular Hough response does not prove the shape is a Voynich rosette.",
            "A long line on an image may be writing, a diagram line, a physical crease or a photographic artifact.",
            "Real fold axes require conservator and codicological confirmation.",
            "Geometrical 2.5D layers remain alternative assumptions, not depth measurements.",
            "The source image color is not historic pigment chemistry."
        ]
    }
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"images_successful":len(evidence),"images_failed":len(failures)}),flush=True)
    return 0 if not failures else 2

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    sys.exit(main(args.output))
