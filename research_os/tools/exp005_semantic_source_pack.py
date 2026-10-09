#!/usr/bin/env python3
"""Build verifiable, source-native blind-review material for Voynich MS408.
Outputs are candidates, NOT historical object classifications or discoveries.
Never accesses the sealed EXP-2026-001 held-out dataset.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw
from exp003_yale_visual_inventory import fetch_image

ROOT=Path(__file__).resolve().parents[1]
CROSS=ROOT/"experiments/EXP-2026-002/yale_archived_jpeg_provenance_crosswalk_2026-10-09.json"
CONTOURS=ROOT/"experiments/EXP-2026-004/structural_roi_source_native_review_queue_2026-10-09.json"
FOLD=ROOT/"experiments/EXP-2026-003/foldout_geometry_probe_2026-10-09.json"
OUT=ROOT/"experiments/EXP-2026-005/native_semantic_review"

FOCUS=[
  ("f67v","67v"),("f85v-86r-foldout","85v and 86r (foldout)"),
  ("f86v-fragment","86v (part) (part of 85-86 foldout)"),
  ("f32r","32r"),("f8v","8v"),("f93r","93r"),
  ("f18v","18v"),("f55r","55r"),("f34v","34v"),
]
PAIRS=[
  ("Q9_TO_Q14_PANORAMA","f67v","f85v-86r-foldout"),
  ("Q9_TO_Q14_FRAGMENT","f67v","f86v-fragment"),
  ("FOLIO32_8","f32r","f8v"),
  ("FOLIO93_18","f93r","f18v"),
  ("NEGATIVE_CONTROL_55_34","f55r","f34v"),
]
# Interior coverage is not learned from matched pairs, so it cannot be
# labelled a specific motif. Deliberate reference windows, not object masks.
WINDOWS=[
  (.16,.19,.30,.29),
  (.53,.19,.30,.29),
  (.16,.54,.30,.28),
  (.53,.54,.30,.28),
]

def strict_interior(box):
    x,y,w,h=[float(v) for v in box]
    return x>=.12 and y>=.09 and x+w<=.88 and y+h<=.91 and w>.025 and h>.025

def bbox_native(norm,w,h):
    x,y,ww,hh=norm
    p=[max(0,int(round(x*w))),max(0,int(round(y*h))),
       min(w,int(round((x+ww)*w))),min(h,int(round((y+hh)*h)))]
    if p[2]-p[0]<40 or p[3]-p[1]<40:
        raise ValueError("Too small ROI on source")
    return p

def crop_and_stats(bgr,box):
    h,w=bgr.shape[:2]
    x0,y0,x1,y1=bbox_native(box,w,h)
    crop=bgr[y0:y1,x0:x1]
    gray=cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY)
    vals=np.percentile(gray,[10,50,90]).round(2).tolist()
    # Pixel edge density is a context-free metric; NOT a historic ink mask.
    small=cv2.resize(gray,(min(480,gray.shape[1]),min(480,gray.shape[0])),
                     interpolation=cv2.INTER_AREA)
    edge=cv2.Canny(small,60,150)
    rgb=cv2.cvtColor(crop,cv2.COLOR_BGR2RGB)
    im=Image.fromarray(rgb)
    im.thumbnail((780,570))
    return im,[x0,y0,x1,y1],{
      "digital_gray_percentiles_10_50_90":vals,
      "digital_edge_fraction":round(float(np.mean(edge>0)),5),
      "color_semantics":"UNKNOWN_PAPER_PIGMENT_NOT_DISAMBIGUATED",
      "historic_object":"UNKNOWN",
      "women_or_stars_or_towers_count":None,
      "true_original_2point5D":None,
    }

def window_for(oid,contours,fold):
    ranked=[]
    seen=[]
    for x in contours:
        if str(x.get("canvas_oid"))!=str(oid):continue
        b=x.get("roi_bbox_xywh_normalized")
        if b and strict_interior(b):
            ranked.append(("MACHINE_CONTOUR_UNVERIFIED",b,x.get("roi_id")))
    for x in fold:
        if str(x.get("canvas_oid"))!=str(oid):continue
        for i,c in enumerate(x.get("candidate_circular_regions",[])):
            b=c.get("box_xywh")
            if b and strict_interior(b):
                ranked.append(("HOUGH_ROUND_REGION_UNVERIFIED",b,f"{oid}:circle:{i}"))
    # Keep two provenance-linked independent proposals when possible.
    # Suppress heavy overlap; then fill with neutral interior review windows.
    out=[]
    for method,box,rid in ranked:
        cx=box[0]+box[2]/2;cy=box[1]+box[3]/2
        if any(abs(cx-(v[0][0]+v[0][2]/2))<.08 and
               abs(cy-(v[0][1]+v[0][3]/2))<.08 for v in seen):
            continue
        seen.append((box,rid));out.append((method,box,rid))
        if len(out)>=2:break
    for i,box in enumerate(WINDOWS):
        cx=box[0]+box[2]/2;cy=box[1]+box[3]/2
        if any(abs(cx-(v[0][0]+v[0][2]/2))<.08 and
               abs(cy-(v[0][1]+v[0][3]/2))<.08 for v in seen):
            continue
        out.append(("NEUTRAL_COVERAGE_GRID_NOT_OBJECT",box,f"{oid}:grid:{i}"))
        seen.append((box,f"{oid}:grid:{i}"))
        if len(out)>=3:break
    assert len(out)==3 and all(strict_interior(box) for _,box,_ in out)
    return out

def image_board(images,ident,title,destination):
    W=830;cell_h=310
    board=Image.new("RGB",(W,64+cell_h*len(images)),(245,244,241))
    draw=ImageDraw.Draw(board)
    draw.text((12,10),title,(20,20,20))
    draw.text((12,30),"ORIGINAL YALE PIXELS; UNVERIFIED SHAPE / NEUTRAL REVIEW WINDOWS",(50,50,50))
    for i,(row,img) in enumerate(images):
        y=64+i*cell_h
        draw.text((10,y+8),f'{i+1}. {row["label"]} / {row["proposal_type"]} / {row["source_oid"]}',(20,20,20))
        board.paste(img,(max(1,(W-img.width)//2),y+34))
    destination.parent.mkdir(parents=True,exist_ok=True)
    board.save(destination,optimize=True)

def build(cross,queue,foldout,out):
    ledger=json.loads(Path(cross).read_text(encoding="utf8"))
    cont=json.loads(Path(queue).read_text(encoding="utf8"))["candidates"]
    folds=json.loads(Path(foldout).read_text(encoding="utf8"))["sources"]
    src={x["yale_label"]:x for x in ledger["archive_files"]}
    assert len(set(x["canvas_oid"] for x in ledger["archive_files"]))==206
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    studies={}
    pages={}
    rows=[]
    for key,label in FOCUS:
        if label not in src:raise ValueError("Missing folio/photo label "+label)
        record=src[label]
        if not record["physical_group_ids"]:raise ValueError("No physical bifolio "+label)
        img=fetch_image(record) # original JPEG SHA-256 reverified by existing fetch_image
        h,w=img.shape[:2]
        oid=str(record["canvas_oid"])
        variants=window_for(oid,cont,folds)
        page_rows=[]
        photo_items=[]
        for i,(method,box,reference) in enumerate(variants):
            picture,px,metrics=crop_and_stats(img,box)
            filename=f"{key}_roi{i+1}.png"
            picture.save(out/filename,optimize=True)
            roi={
                "crop_id":f"{key}:R{i+1}",
                "source_oid":oid,"label":label,"physical_groups":record["physical_group_ids"],
                "source_jpeg_sha256":record["imported_reported_sha256"],
                "original_jpeg_path":record["path"],
                "original_resolution_px":[w,h],
                "proposal_type":method,"original_roi_reference":reference,
                "bbox_normalized_xywh":[round(float(q),6) for q in box],
                "bbox_source_native_xyxy_px":px,
                "crop_path":filename,
                "image_crop_sha256":hashlib.sha256((out/filename).read_bytes()).hexdigest(),
                "source_verified_this_execution":True,
                "descriptive_features":metrics,
                "annotation_status":"MACHINE_OR_GRID_PROPOSAL_NOT_HUMAN_VALIDATED",
                "semantic_review_pass_1":"NOT_RUN",
                "semantic_review_pass_2":"NOT_RUN",
                "keeper_review":"NOT_RUN",
                "same_historical_object":"NOT_ESTABLISHED",
            }
            rows.append(roi);page_rows.append(roi);photo_items.append((roi,picture))
        studies[key]=photo_items
        pages[key]={"label":label,"oid":oid,"physical_groups":record["physical_group_ids"],
                    "source_sha256":record["imported_reported_sha256"],
                    "crop_ids":[x["crop_id"] for x in page_rows]}
        print("SEMANTIC_REVIEW_SOURCE",key,label,oid,"CROPS",len(page_rows),flush=True)
    links=[]
    for id,left,right in PAIRS:
        if set(pages[left]["physical_groups"]) & set(pages[right]["physical_groups"]):
            raise ValueError("Physical group leakage: "+id)
        base=(studies[left][:2]+studies[right][:2])
        target=out/(id.lower()+"_comparison_board.png")
        image_board(base,id,f"{left} versus {right}: SOURCE REVIEW ONLY",target)
        links.append({"comparison":id,"left":left,"right":right,
                      "comparison_board":target.name,
                      "human_same_object_assessed":False,
                      "2point5d_test_status":"NOT_RUN",
                      "decision":"INSUFFICIENT_SEMANTIC_EVIDENCE"})
    pageboard=out/"all_primary_native_crops_contact_sheet.png"
    image_board([(r,img) for group in studies.values() for r,img in group],
                "all","PRIMARY CROP MANIFEST",pageboard)
    report={
       "schema":"voynich-exp005-source-native-semantic-review-starter-v1",
       "scientific_status":"AWAITING_INDEPENDENT_SEMANTIC_REVIEW",
       "provenance":{"crosswalk_sha256":hashlib.sha256(Path(cross).read_bytes()).hexdigest(),
          "contour_queue_sha256":hashlib.sha256(Path(queue).read_bytes()).hexdigest(),
          "foldout_probe_sha256":hashlib.sha256(Path(foldout).read_bytes()).hexdigest()},
       "source_photos":len(studies),"source_native_crops":len(rows),
       "primary_comparisons":links,"review_photos":pages,
       "proposed_regions":rows,
       "four_null_models":{
            "count_only":"NOT_RUN","color_only":"NOT_RUN",
            "outline_only":"NOT_RUN","text_only":"NOT_RUN"},
       "blind_human_ground_truth":False,
       "separate_AI_semantic_passes":"NOT_RUN",
       "historical_star_woman_tower_count":"UNKNOWN",
       "source_heldout_used":False,
       "accepted_MV3":0,"accepted_MV4":0,
       "warnings":["Grid windows sample interiors without claiming object location.",
          "Contour/Hough proposals may be noise; every candidate needs independent semantic review.",
          "Digital edge fraction and grayscale percentiles are not pigment, manuscript text or object identity.",
          "No independent annotation, null-test significance or multiple comparison correction yet."]
    }
    (out/"review_manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    assert report["source_native_crops"]>=12
    assert report["accepted_MV3"]==report["accepted_MV4"]==0
    print("SEMANTIC_NATIVE_STAGING_PASS","PHOTOS",len(studies),
          "CROPS",len(rows),"PAIRS",len(links),"MV3",0,flush=True)
    return report

def selftest():
    assert strict_interior([.2,.2,.3,.3])
    assert not strict_interior([0,.2,.3,.3])
    assert not strict_interior([.7,.8,.4,.3])
    assert bbox_native([.2,.2,.3,.3],1000,1000)==[200,200,500,500]
    generated=window_for("none",[],[])
    assert len(generated)==3 and all(p[0]=="NEUTRAL_COVERAGE_GRID_NOT_OBJECT" for p in generated)
    print("SEMANTIC_NATIVE_SELFTEST_PASS",flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--crosswalk",default=str(CROSS))
    p.add_argument("--contours",default=str(CONTOURS))
    p.add_argument("--foldout",default=str(FOLD))
    p.add_argument("--out",default=str(OUT))
    p.add_argument("--selftest",action="store_true")
    a=p.parse_args()
    if a.selftest:selftest()
    else:build(a.crosswalk,a.contours,a.foldout,a.out)
