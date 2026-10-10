#!/usr/bin/env python3
"""Structural ROI follow-up: photo-border controls and source-native review.
Automated contour silhouettes are NOT historical objects or semantic labels.
"""
from __future__ import annotations
import argparse
import itertools
import json
import math
from pathlib import Path
import cv2
from PIL import Image,ImageDraw
from exp003_yale_visual_inventory import fetch_image
from mv_discovery_targeted import orb_features,orb_geometric_match,as_panel

ROOT=Path(__file__).resolve().parents[1]
QUEUE=ROOT/"experiments"/"EXP-2026-004"/"structural_roi_source_native_review_queue_2026-10-09.json"
LEDGER=ROOT/"experiments"/"EXP-2026-002"/"yale_archived_jpeg_provenance_crosswalk_2026-10-09.json"
SECTIONS=ROOT/"experiments"/"EXP-2026-001"/"section_assignments.json"
OUT=ROOT/"experiments"/"EXP-2026-004"/"mv_contour_followup"

def interior_roi(c,strict=True):
    x,y,w,h=[float(z) for z in c["roi_bbox_xywh_normalized"]]
    if not (0<=x<=1 and 0<=y<=1 and 0<w<=1-x and 0<h<=1-y):
        return False
    if strict:
        return x>=.10 and y>=.07 and x+w<=.90 and y+h<=.93
    return True

def eligible(a,b):
    if str(a["canvas_oid"])==str(b["canvas_oid"]):return False
    if not a.get("physical_group_ids") or not b.get("physical_group_ids"):return False
    if set(a["physical_group_ids"]) & set(b["physical_group_ids"]):return False
    if a["shape_class_machine"]!=b["shape_class_machine"]:return False
    aw,ah=a["roi_bbox_xywh_normalized"][2:4]
    bw,bh=b["roi_bbox_xywh_normalized"][2:4]
    return all(v>0 for v in (aw,ah,bw,bh)) and abs(math.log((aw/ah)/(bw/bh)))<=.5

def hamming64(a,b):
    if len(a)!=16 or len(b)!=16:raise ValueError("dHash missing")
    return (int(a,16)^int(b,16)).bit_count()

def extract(bgr,c,pad=.35):
    x,y,w,h=[float(z) for z in c["roi_bbox_xywh_normalized"]]
    H,W=bgr.shape[:2]
    x0=max(0,round((x-w*pad)*W));y0=max(0,round((y-h*pad)*H))
    x1=min(W,round((x+w*(1+pad))*W));y1=min(H,round((y+h*(1+pad))*H))
    if x1-x0<20 or y1-y0<20:raise ValueError("Tiny crop")
    crop=bgr[y0:y1,x0:x1].copy()
    scale=min(1.,720/max(crop.shape[:2]))
    if scale<1:
        crop=cv2.resize(crop,(round(crop.shape[1]*scale),round(crop.shape[0]*scale)),interpolation=cv2.INTER_AREA)
    return crop,[x0,y0,x1,y1]

def figure_board(pairs,images,rows,destination):
    count=len(pairs);height=51+355*count
    board=Image.new("RGB",(810,height),(248,246,241))
    draw=ImageDraw.Draw(board)
    draw.text((10,12),"SOURCE ORIGINAL ROI - CROSS FOLIO. NOT VALIDATED SAME OBJECT",(30,30,30))
    for i,p in enumerate(pairs):
        y=51+i*355
        a,b=rows[p["roi_a"]],rows[p["roi_b"]]
        draw.text((8,y+7),f'{i+1}: {p["folio_a"]} <> {p["folio_b"]} | contour dHash {p["hamming_64"]}/64 | inliers {p["native_rigid_inliers"]}',(30,30,30))
        draw.text((8,y+25),f'Section: {p["section_relation"]} | counts, colors, text, faces: NOT ASSESSED',(65,65,65))
        board.paste(as_panel(images[p["roi_a"]]),(10,y+46))
        board.paste(as_panel(images[p["roi_b"]]),(415,y+46))
        draw.text((10,y+340),p["roi_a"][:52]+" / "+p["roi_b"][:52],(80,80,80))
    destination.parent.mkdir(parents=True,exist_ok=True)
    board.save(destination)
    return count

def run(queue,ledger,sections,destination,max_pairs=12):
    d=json.loads(Path(queue).read_text(encoding="utf8"))
    l=json.loads(Path(ledger).read_text(encoding="utf8"))
    s=json.loads(Path(sections).read_text(encoding="utf8"))
    assert d["counts"]["structural_contour_candidates"]==229
    all_rois=d["candidates"]
    clean=[c for c in all_rois if interior_roi(c) and c.get("physical_group_ids") and "cover" not in c["folio_label"].lower()]
    source={str(x["canvas_oid"]):x for x in l["archive_files"]}
    sec={x["folio_id"]:x["section_label"] for x in s["records"]}
    raw_pairs=[]
    for a,b in itertools.combinations(clean,2):
        if not eligible(a,b):continue
        dist=hamming64(a["shape_hash_dhash64"],b["shape_hash_dhash64"])
        if dist>18:continue
        raw_pairs.append({
            "roi_a":a["roi_id"],"roi_b":b["roi_id"],
            "folio_a":a["folio_label"],"folio_b":b["folio_label"],
            "canvas_a":str(a["canvas_oid"]),"canvas_b":str(b["canvas_oid"]),
            "original_bbox_a":a["roi_bbox_xywh_native_pixels"],
            "original_bbox_b":b["roi_bbox_xywh_native_pixels"],
            "physical_groups_a":a["physical_group_ids"],"physical_groups_b":b["physical_group_ids"],
            "proposed_shape_class":a["shape_class_machine"],
            "hamming_64":dist,"roundness_difference":round(abs(a["roundness"]-b["roundness"]),4),
            "section_a":sec.get(a["folio_label"],"UNKNOWN"),
            "section_b":sec.get(b["folio_label"],"UNKNOWN"),
            "section_relation":"NOT_ASSIGNED",
            "semantic_identity":"NOT_ESTABLISHED",
            "mv_candidate_class":"MV0_MV1_ONLY",
        })
    for p in raw_pairs:
        if p["section_a"]=="UNKNOWN" or p["section_b"]=="UNKNOWN":
            p["section_relation"]="UNKNOWN"
        elif p["section_a"]==p["section_b"]:
            p["section_relation"]="WITHIN"
        else:
            p["section_relation"]="BETWEEN"
    raw_pairs.sort(key=lambda p:(p["hamming_64"],p["roundness_difference"],p["roi_a"],p["roi_b"]))
    unique=[]
    used=set()
    for p in raw_pairs:
        key=tuple(sorted([p["canvas_a"],p["canvas_b"]]))
        if key in used:continue
        unique.append(p);used.add(key)
        if len(unique)>=max_pairs:break
    records={c["roi_id"]:c for c in all_rois}
    seen={}
    images={}
    for p in unique:
        for id in (p["roi_a"],p["roi_b"]):
            c=records[id];oid=str(c["canvas_oid"])
            if oid not in source:raise RuntimeError(f"Missing source image {oid}")
            if c["original_sha256"] != source[oid]["imported_reported_sha256"]:
                raise RuntimeError("Source digest mismatch")
            if oid not in seen:seen[oid]=fetch_image(source[oid])
            crop,box=extract(seen[oid],c)
            images[id]=crop
            p["native_source_bbox_"+("a" if id==p["roi_a"] else "b")]=box
        x=orb_geometric_match(orb_features(images[p["roi_a"]]),
                              orb_features(images[p["roi_b"]]))
        p["native_rigid_inliers"]=x["rigid_ransac_inliers"]
        p["native_rigid_fraction"]=x["rigid_inlier_fraction"]
        p["geometry_review"]=x["evidence"]
        p["source_jpegs_sha256_rechecked"]=True
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    preview=destination/"contour_review_board.png"
    count=figure_board(unique,images,records,preview)
    report={
        "scientific_status":"EXPLORATORY_NOT_CONFIRMED",
        "source_candidates":len(all_rois),"strict_interior_contours":len(clean),
        "distinct_physical_pair_candidates_hamming_le18":len(raw_pairs),
        "source_photos_sha256_rechecked":len(seen),
        "review_pairs":count,
        "unique_pair_review_list":unique,
        "within_section_pairs":sum(p["section_relation"]=="WITHIN" for p in raw_pairs),
        "between_section_pairs":sum(p["section_relation"]=="BETWEEN" for p in raw_pairs),
        "section_unknown_pairs":sum(p["section_relation"]=="UNKNOWN" for p in raw_pairs),
        "review_board":str(preview),
        "null_count_only":"NOT_ASSESSED",
        "null_color_only":"NOT_ASSESSED",
        "null_outline_only":"DESCRIPTIVE_DHASH_SCREEN_ONLY",
        "null_text_only":"NOT_ASSESSED",
        "semantic_labels_human_confirmed":0,
        "mv2_or_higher_verdicts":0,
        "source_held_out_used":False,
        "cautions":[
            "Raw 960px contour ROI machine proposals are not historical boundaries or specific illustration classes",
            "Strict margin exclusion can eliminate real ornaments; preserve rejected items for separate margin track",
            "dHash is not view invariant; paired photographs require independent semantic object masks",
            "Native ORB rigid 2D evidence cannot alone prove identical objects or historical 3D projection",
            "Multiple-pair search and self-selection mean no inferential significance has been computed"
        ]
    }
    (destination/"contour_screen_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("MV_CONTOUR_DISCOVERY",len(all_rois),"INTERIOR",len(clean),
          "PAIRS",len(raw_pairs),"REVIEW",len(unique),
          "RIGID_GE5",sum(x["native_rigid_inliers"]>=5 for x in unique),
          "WITHIN",report["within_section_pairs"],"BETWEEN",report["between_section_pairs"])
    for p in unique[:12]:
        print("CONTOUR_REVIEW",p["folio_a"],p["folio_b"],p["hamming_64"],
              p["native_rigid_inliers"],p["section_relation"])
    return report

def selftest():
    c={"roi_bbox_xywh_normalized":[.2,.2,.1,.1]}
    assert interior_roi(c) and not interior_roi({"roi_bbox_xywh_normalized":[0,.1,.1,.1]})
    a={"canvas_oid":"1","physical_group_ids":["A"],"shape_class_machine":"shape","roi_bbox_xywh_normalized":[.2,.2,.1,.1]}
    b={**a,"canvas_oid":"2","physical_group_ids":["B"]}
    assert eligible(a,b)
    assert not eligible(a,{**b,"physical_group_ids":["A"]})
    assert hamming64("0000000000000000","ffffffffffffffff")==64
    assert hamming64("0000000000000000","0000000000000000")==0
    print("MV_CONTOUR_SELFTEST_PASS")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--queue",default=str(QUEUE))
    p.add_argument("--ledger",default=str(LEDGER))
    p.add_argument("--sections",default=str(SECTIONS))
    p.add_argument("--out",default=str(OUT))
    p.add_argument("--selftest",action="store_true")
    a=p.parse_args()
    if a.selftest:selftest()
    else:run(a.queue,a.ledger,a.sections,a.out)
