#!/usr/bin/env python3
"""EXP006 — genuinely separate image-segmentation proposals for blind source review.

These are NOT semantic annotations or two independent human interpretations.
The output contains pixel-bounded polygons, source-coordinate provenance and
explicit blank reviewer forms. It must never be called a decoded Voynich object.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"experiments/EXP-2026-005/native_semantic_review"
OUT=ROOT/"experiments/EXP-2026-006/blind_object_review"
METHODS=("A_LOCAL_INK","B_MULTISCALE_BLACKHAT")
CLASSES=("UNKNOWN","architecture","rosette","plant_part","person","ornament","writing","other")

def isolated_mask(image,method):
    gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    gray=cv2.GaussianBlur(gray,(3,3),0)
    if method=="A_LOCAL_INK":
        out=cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY_INV,35,11)
    elif method=="B_MULTISCALE_BLACKHAT":
        k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(19,19))
        dark=cv2.morphologyEx(gray,cv2.MORPH_BLACKHAT,k)
        _,out=cv2.threshold(dark,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        out=cv2.morphologyEx(out,cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
    else:raise ValueError("Unsupported segmentation")
    return cv2.dilate(out,np.ones((2,2),np.uint8),iterations=1)

def find_shapes(image,method,maximum=10):
    mask=isolated_mask(image,method)
    H,W=mask.shape
    contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    found=[]
    for c in contours:
        area=float(cv2.contourArea(c))
        x,y,w,h=cv2.boundingRect(c)
        if area<max(30,H*W*.00018) or area>H*W*.24:continue
        if w<9 or h<9 or x<4 or y<4 or x+w>W-4 or y+h>H-4:continue
        eps=.012*cv2.arcLength(c,True)
        poly=cv2.approxPolyDP(c,eps,True).reshape(-1,2).tolist()
        if len(poly)<3:continue
        found.append({"crop_bbox_xyxy":[x,y,x+w,y+h],
                      "crop_polygon_xy":poly,
                      "pixel_contour_area":round(area,2),
                      "crop_area_fraction":round(area/(H*W),7),
                      "algorithmic_label":"INK_COMPONENT_PROPOSAL",
                      "semantic_label":"UNKNOWN",
                      "annotation_status":"NOT_SEMANTICALLY_REVIEWED",
                      "is_person":None,"is_tower":None,"ring_count":None,
                      "branch_port_count":None,"face_direction":None,
                      "scribal_token":None})
    found.sort(key=lambda s:-s["pixel_contour_area"])
    return found[:maximum]

def image_to_original(shape,crop_size,source_bbox):
    W,H=crop_size
    x0,y0,x1,y1=source_bbox
    sx=(x1-x0)/W;sy=(y1-y0)/H
    x,y,rx,ry=shape["crop_bbox_xyxy"]
    return {"original_photo_bbox_xyxy":[round(x0+x*sx),round(y0+y*sy),
                                          round(x0+rx*sx),round(y0+ry*sy)],
            "original_photo_polygon_xy":[[round(x0+px*sx),round(y0+py*sy)]
                                          for px,py in shape["crop_polygon_xy"]]}

def iou(a,b):
    x=max(a[0],b[0]);y=max(a[1],b[1]);r=min(a[2],b[2]);d=min(a[3],b[3])
    inter=max(0,r-x)*max(0,d-y)
    aa=max(0,a[2]-a[0])*max(0,a[3]-a[1])
    bb=max(0,b[2]-b[0])*max(0,b[3]-b[1])
    return inter/(aa+bb-inter) if aa+bb>inter else 0.

def relations(items):
    # Different ink fragments may form an object or not: no false object graph.
    res=[]
    for i,a in enumerate(items):
        ax,ay,ar,ad=a["original_photo_bbox_xyxy"]
        aw=max(1,ar-ax);ah=max(1,ad-ay)
        for b in items[i+1:]:
            bx,by,br,bd=b["original_photo_bbox_xyxy"]
            bw=max(1,br-bx);bh=max(1,bd-by)
            ca=((ax+ar)/2,(ay+ad)/2);cb=((bx+br)/2,(by+bd)/2)
            relation="overlaps" if iou([ax,ay,ar,ad],[bx,by,br,bd])>0 else (
                     "left_of" if ca[0]<cb[0] else "right_of")
            res.append({"a":a["proposal_id"],"b":b["proposal_id"],
                        "image_box_relation":relation,
                        "normalized_centroid_distance":round(math.hypot((ca[0]-cb[0])/(aw+bw),
                                                                       (ca[1]-cb[1])/(ah+bh)),4),
                        "semantic_connection":"UNKNOWN_NOT_OBSERVED"})
    return res

def overlay(image,shapes,method):
    base=Image.fromarray(cv2.cvtColor(image,cv2.COLOR_BGR2RGB))
    pen=ImageDraw.Draw(base)
    for p in shapes:
        poly=[tuple(q) for q in p["crop_polygon_xy"]]
        pen.line(poly+[poly[0]],fill=(195,24,33) if method==METHODS[0] else (22,87,209),width=3)
        x,y,*_=p["crop_bbox_xyxy"]
        pen.text((x,y),str(p["proposal_id"].split(":")[-1]),fill=(255,0,0))
    return base

def build(source,out):
    source=Path(source);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    j=json.loads((source/"review_manifest.json").read_text(encoding="utf8"))
    assert j["source_photos"]==9 and j["source_native_crops"]==27
    outputs={m:[] for m in METHODS}
    graph={}
    comparison=[]
    by_photo={}
    img_count=0
    for roi in j["proposed_regions"]:
        crop=source/roi["crop_path"]
        if hashlib.sha256(crop.read_bytes()).hexdigest()!=roi["image_crop_sha256"]:
            raise ValueError("Crop SHA integrity failed")
        photo=cv2.imread(str(crop))
        if photo is None:raise ValueError("Cannot decode crop "+str(crop))
        h,w=photo.shape[:2]
        key=roi["crop_id"];img_count+=1
        sequences={}
        for method in METHODS:
            shapes=find_shapes(photo,method)
            rows=[]
            for i,s in enumerate(shapes,1):
                s["proposal_id"]=f"{key}:{method}:{i}"
                s.update(image_to_original(s,[w,h],roi["bbox_source_native_xyxy_px"]))
                s["source_oid"]=roi["source_oid"]
                s["physical_groups"]=roi["physical_groups"]
                s["source_jpeg_sha256"]=roi["source_jpeg_sha256"]
                s["cropped_file_sha256"]=roi["image_crop_sha256"]
                s["source_crop_id"]=key
                s["method"]=method
                rows.append(s)
                outputs[method].append(s)
            sequences[method]=rows
            graph[f"{key}:{method}"]=relations(rows)
            by_photo.setdefault(key,{}).update({method:(photo,rows)})
        aa,bb=sequences[METHODS[0]],sequences[METHODS[1]]
        used=set();overlaps=[]
        for a in aa:
            options=[(iou(a["crop_bbox_xyxy"],b["crop_bbox_xyxy"]),b)
                     for b in bb if b["proposal_id"] not in used]
            if not options:continue
            match,b=max(options,key=lambda p:p[0])
            if match>=.35:
                overlaps.append({"proposal_a":a["proposal_id"],"proposal_b":b["proposal_id"],
                                 "bbox_iou":round(match,4),
                                 "classification_consensus":"NOT_ASSESSED"})
                used.add(b["proposal_id"])
        comparison.append({"crop_id":key,"photo_oid":roi["source_oid"],
                           "candidate_counts":{m:len(sequences[m]) for m in METHODS},
                           "bbox_agreements_ge_0_35":len(overlaps),
                           "geometric_candidate_overlaps":overlaps,
                           "human_semantic_agreement":"NOT_ASSESSED",
                           "blinded_semantic_pass_A":"NOT_PERFORMED",
                           "blinded_semantic_pass_B":"NOT_PERFORMED"})
        # Two evidence overlay panels per crop: never annotated as object class.
        for method,(im,rows) in by_photo[key].items():
            result=overlay(im,rows,method)
            result.save(out/(key.replace(":","_")+"_"+method+".png"),optimize=True)
        print("EXP006_CROP",key,len(aa),len(bb),"MATCHED",len(overlaps),flush=True)
    for method in METHODS:
        (out/(method.lower()+"_proposals.json")).write_text(
            json.dumps({"method":method,"role":"PIXEL_MASK_PROPOSALS_NOT_BLIND_SEMANTIC_ANNOTATION",
                        "proposals":outputs[method]},ensure_ascii=False,indent=2)+"\n",
            encoding="utf8")
    summary={
        "schema":"exp006-source-provenance-blind-review-queue-v1",
        "scientific_status":"MACHINE_GEOMETRY_ONLY_SEMANTIC_REVIEW_NOT_PERFORMED",
        "original_yale_photo_count":j["source_photos"],
        "source_sha_check":"UPSTREAM_JPEG_SHA256_RECOMPUTED_IN_THIS_WORKFLOW",
        "crop_sha_check":"SHA256_RECOMPUTED_AND_MATCHED",
        "verified_crops":img_count,
        "two_independent_algorithmic_proposals":True,
        "two_independent_semantic_interpretations":False,
        "blinded_human_annotation_count":0,
        "historical_object_classification":"UNKNOWN",
        "sources_exp001_heldout_used":False,
        "source_photographs":j["review_photos"],
        "paired_folios":j["primary_comparisons"],
        "annotation_crops":comparison,
        "proposal_counts":{m:len(outputs[m]) for m in METHODS},
        "text_roi_registration":"NOT_ASSESSED",
        "historical_multi_view_identity":"NOT_ESTABLISHED",
        "accepted_mv2":0,"accepted_mv3":0,"accepted_mv4":0,
        "warnings":[
            "Both methods are low-level pixel algorithms rather than independent human or vision-model semantic annotators.",
            "Individual connected components cannot be assumed to correspond to complete historic objects.",
            "Neutral sample windows and paper/ink artifacts can be mistaken for illustrations.",
            "Image-box relations and digital ink junctions are not validated graph connections in the depicted scene.",
            "Historic star/tower/figure counts are UNKNOWN, not zero."
        ]
    }
    (out/"disagreement_and_review_queue.json").write_text(
        json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    (out/"machine_spatial_component_relations.json").write_text(
        json.dumps(graph,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    labels={
      "schema":"exp006-blind-human-semantic-review-form-v1",
      "instructions":"Review original Yale full scan without pair identities or algorithm ranks; use UNKNOWN rather than guesses. Fill only after actual independent image inspection.",
      "allowed_classes":list(CLASSES),
      "reviewer_1":{"reviewer_id":None,"proposals_reviewed":[],
                    "source_photo_verified":False,"reviewed_at":None},
      "reviewer_2":{"reviewer_id":None,"proposals_reviewed":[],
                    "source_photo_verified":False,"reviewed_at":None},
      "independent_semantic_agreement":"NOT_ASSESSED",
      "keeper_adjudication":"NOT_ASSESSED",
      "source_roi_reference":"disagreement_and_review_queue.json"
    }
    (out/"blind_reviewer_annotation_form.json").write_text(
        json.dumps(labels,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("EXP006_SOURCE_REVIEW_PACK",img_count,"CROPS",
          "PASS_A",len(outputs[METHODS[0]]),"PASS_B",len(outputs[METHODS[1]]),
          "HUMAN_SEMANTIC",0,flush=True)
    return summary

def selftest():
    im=np.full((250,250,3),230,np.uint8)
    cv2.rectangle(im,(35,35),(95,95),(15,15,15),4)
    cv2.circle(im,(160,155),32,(20,20,20),4)
    for method in METHODS:
        shapes=find_shapes(im,method)
        assert isinstance(shapes,list)
        assert all(s["semantic_label"]=="UNKNOWN" and s["is_person"] is None for s in shapes)
    a={"crop_bbox_xyxy":[20,20,60,60],"crop_polygon_xy":[[20,20],[60,20],[60,60],[20,60]]}
    mapped=image_to_original(a,[100,100],[1000,1000,1100,1100])
    assert mapped["original_photo_bbox_xyxy"]==[1020,1020,1060,1060]
    assert abs(iou([0,0,10,10],[0,0,10,10])-1)<1e-6
    print("EXP006_SOURCE_REVIEW_SELFTEST_PASS",flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",default=str(SOURCE))
    p.add_argument("--out",default=str(OUT))
    p.add_argument("--selftest",action="store_true")
    a=p.parse_args()
    if a.selftest:selftest()
    else:build(a.source,a.out)
