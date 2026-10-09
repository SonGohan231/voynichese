#!/usr/bin/env python3
"""EXP004 Native image review packets for people, architecture, and rosettes.

This intentionally does not pretend to recognize people, towers, merlons,
stars, gestures or orientation. It creates source-matched, full-native-pixel
annotation targets, evidence links and an empty independent-review ledger.

Human annotation is the decisive missing step for all semantic counts and
cross-perspective identity claims. Prior heldout EXP001/002 not consulted.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from exp003_yale_visual_inventory import fetch_image

ROOT=Path(__file__).resolve().parents[1]
E2=ROOT/"experiments"/"EXP-2026-002"
E3=ROOT/"experiments"/"EXP-2026-003"
E4=ROOT/"experiments"/"EXP-2026-004"
CROSS=E2/"yale_archived_jpeg_provenance_crosswalk_2026-10-09.json"
FOLD=E3/"foldout_geometry_probe_2026-10-09.json"
PRIORITY=[
    ("1006195","roundel_and_astral","f67v"),
    ("1006197","roundel_and_astral","f68v"),
    ("1006231","architecture_rosette_and_towers","f85v-f86r"),
    ("1006209","people_heads_and_gestures","f75v"),
    ("1006214","people_heads_and_gestures","f78r"),
    ("1006216","people_heads_and_gestures","f79r"),
]
LABELS={
 "roundel_and_astral":["ring","spoke","sector","star_motif","number_of_star_points","label","unknown"],
 "architecture_rosette_and_towers":["tower","merlon","perimeter","junction","ornament","ring","sector","star","unknown"],
 "people_heads_and_gestures":["figure","head","face","arm","body_axis","overlap","duct","unknown"],
}
FIELDS=("reviewer_id","source_id","tile_id","object_id","object_type",
        "polygon_tile_pixel_xy","face_left_right_front","body_axis_deg",
        "gaze_deg","other_person_or_object_relation","ring_count","sector_count",
        "star_count","merlon_count","paint_state","text_label_or_token","confidence",
        "reviewer_notes")

def normalized_box(col,row,cols=3,rows=3):
    return [round(col/cols,6),round(row/rows,6),
            round(1/cols,6),round(1/rows,6)]

def iiif_uri(oid,bbox):
    x,y,w,h=bbox
    return ("https://collections.library.yale.edu/iiif/2/"
            f"{oid}/pct:{x*100:.4f},{y*100:.4f},{w*100:.4f},{h*100:.4f}"
            "/!1200,1200/0/default.jpg")

def native_crop(bgr,bbox):
    h,w=bgr.shape[:2];x,y,bw,bh=bbox
    xx=round(x*w);yy=round(y*h)
    right=min(w,round((x+bw)*w));bottom=min(h,round((y+bh)*h))
    return bgr[max(0,yy):bottom,max(0,xx):right].copy(),[xx,yy,right-xx,bottom-yy]

def save_tile(bgr,path,maxwidth=1000):
    h,w=bgr.shape[:2]
    resize=min(1.,maxwidth/max(w,h))
    if resize<1.:
        bgr=cv2.resize(bgr,(round(w*resize),round(h*resize)),interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(path),bgr,[int(cv2.IMWRITE_JPEG_QUALITY),90])
    return [bgr.shape[1],bgr.shape[0]]

def build_overview(bgr,source_id,section,tile_n=3):
    img=Image.fromarray(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB))
    img.thumbnail((1120,1120))
    pad=70
    sheet=Image.new("RGB",(img.width,img.height+pad),"#f6f4ef")
    sheet.paste(img,(0,pad))
    d=ImageDraw.Draw(sheet)
    d.text((12,9),f"EXP004 source {source_id}  |  {section}",fill="#242424")
    d.text((12,33),"GRID IS FOR REVIEW ONLY: every box is UNLABELLED until independently annotated.",fill="#454545")
    for i in range(1,tile_n):
        x=round(i*img.width/tile_n)
        y=pad+round(i*img.height/tile_n)
        d.line((x,pad,x,img.height+pad),fill="#e44040",width=2)
        d.line((0,y,img.width,y),fill="#e44040",width=2)
    for yy in range(tile_n):
        for xx in range(tile_n):
            cx=round((xx+.03)*img.width/tile_n)
            cy=pad+round((yy+.03)*img.height/tile_n)
            d.rectangle((cx-3,cy-2,cx+52,cy+21),fill="#f3f2ee")
            d.text((cx,cy),f"{yy}{xx}",fill="#111111")
    return sheet

def review_packets(cross,foldout,out,limit=None):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    ledger=json.loads(Path(cross).read_text(encoding="utf-8"))
    src={str(e["canvas_oid"]):e for e in ledger["archive_files"]}
    fold=json.loads(Path(foldout).read_text(encoding="utf-8"))
    circles={str(e["canvas_oid"]):e for e in fold["sources"]}
    priority=PRIORITY[:limit] if limit else PRIORITY
    targets=[];pages=[];source_sha={}
    for oid,category,short in priority:
        entry=src[oid]
        im=fetch_image(entry)
        h,w=im.shape[:2]
        if (h<1500 or w<1500):
            raise ValueError("Original source photo unexpectedly small")
        source_sha[oid]=entry["imported_reported_sha256"]
        sheet=build_overview(im,oid,category)
        overview=out/f"source_{oid}_{short}_grid.png"
        sheet.save(overview)
        pages.append({"source_oid":oid,"folio_label":entry["yale_label"],
                      "physical_groups":entry.get("physical_group_ids",[]),
                      "original_dimensions_wh":[w,h],
                      "archive_path":entry["path"],
                      "verified_source_jpeg_sha256":source_sha[oid],
                      "category_for_manual_inspection":category,
                      "overview":overview.name,
                      "automated_human_count":None,
                      "review_verdict":"UNOBSERVED"})
        for yy in range(3):
            for xx in range(3):
                tileid=f"{oid}:r{yy}c{xx}"
                box=normalized_box(xx,yy)
                raw,pixbbox=native_crop(im,box)
                file=out/f"{oid}_r{yy}c{xx}.jpg"
                imsize=save_tile(raw,file)
                targets.append({
                    "source_id":oid,"folio_label":entry["yale_label"],
                    "category_for_manual_inspection":category,"tile_id":tileid,
                    "physical_groups":entry.get("physical_group_ids",[]),
                    "source_jpeg_sha256":source_sha[oid],
                    "native_pixel_bbox_xywh":pixbbox,
                    "source_fraction_bbox_xywh":box,
                    "review_image":file.name,
                    "saved_review_image_wh":imsize,
                    "iiif_native_crop_reference":iiif_uri(oid,box),
                    "suggested_annotation_object_types":LABELS[category],
                    "annotator_A":"NOT_STARTED","annotator_B":"NOT_STARTED",
                    "agreed_n_objects":None,"face_orientation_count":None,
                    "star_count":None,"tower_count":None,
                    "acceptance":"PENDING_TWO_INDEPENDENT_ANNOTATORS",
                })
        print("SOURCE_CROPS",oid,entry["yale_label"],"9",flush=True)
    # Hough proposals are appended as additional REVIEW TARGETS, NOT counts.
    circle_targets=[]
    for p in pages:
        oid=p["source_oid"]
        if oid not in circles:continue
        for j,c in enumerate(circles[oid].get("candidate_circular_regions",[])):
            rad=c["radius_fraction_of_minimum_axis"]
            cx,cy=c["center_xy"]
            circle_targets.append({
                "source_id":oid,"folio_label":p["folio_label"],
                "candidate_id":f"{oid}:hough:{j}","center_image_fraction":[cx,cy],
                "radius_fraction_of_short_image_axis":rad,
                "radial_edge_support":c.get("edge_support_fraction"),
                "class":"HOUGH_ROUND_FEATURE_NOT_A_VALIDATED_ROSETTE",
                "verified_actual_ring_count":None,
                "verified_spoke_count":None,
                "verified_star_count":None,
                "verified_female_figure_count":None,
                "native_full_source_iiif":f"https://collections.library.yale.edu/iiif/2/{oid}/full/full/0/default.jpg",
                "manual_adjudication":"PENDING",
            })
    with (out/"blank_independent_annotations.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader()
    schema={
      "schema":"voynich-exp004-native-review-packet-v1",
      "purpose":"Object-level manual blind annotation before any claim same object other perspective",
      "source_archive_index_sha256":hashlib.sha256(Path(cross).read_bytes()).hexdigest(),
      "prior_foldout_detector_sha256":hashlib.sha256(Path(foldout).read_bytes()).hexdigest(),
      "source_photos_count":len(pages),"review_tiles_count":len(targets),
      "hough_unverified_round_feature_count":len(circle_targets),
      "no_physical_unit_heldout_exposed":True,
      "source_pages":pages,"review_targets":targets,"unverified_round_features":circle_targets,
      "required_controls":[
        "Two independent blind annotators must explicitly label real drawn objects and orient heads",
        "Rings, sectors, star points, merlons and figures are not counted automatically",
        "Document zero only if entire source crop has been visually inspected; otherwise use null",
        "Source-original paper color not chemically calibrated; uncolored != no semantic attribute",
        "Compare different physical bifolios and independent scribe section controls",
        "Occlusion, junction and different-view logic requires adjudicated source-native polylines",
        "Photo/image borders excluded from object claims, marginal drawn decoration may still be real",
        "Do not use images selected after inspection as untouched statistical heldout"
      ],
      "scientific_verdict":"UNANNOTATED_NO_OBJECT_IDENTITY_CLAIM",
    }
    (out/"native_annotation_packet_index.json").write_text(
        json.dumps(schema,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("EXP004_NATIVE_REVIEW_PACKET",len(pages),"SOURCES",len(targets),"TILES",
          len(circle_targets),"UNVERIFIED_ROUND_PROPOSALS",
          "SCIENCE",schema["scientific_verdict"],flush=True)

def selftest():
    a=normalized_box(1,1)
    assert a==[.333333,.333333,.333333,.333333]
    img=np.zeros((230,300,3),np.uint8)
    tile,pix=native_crop(img,[.3,.2,.4,.5])
    assert pix==[90,46,120,115],pix
    assert tile.shape[:2]==(115,120)
    assert "/pct:" in iiif_uri("123",a)
    v=build_overview(img,"123","test")
    assert v.size[0]>0 and v.size[1]>0
    print("EXP004_NATIVE_PACKET_SELFTEST_PASS grids, pixel crop, blank labels, IIIF")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--crosswalk",default=str(CROSS))
    p.add_argument("--foldout",default=str(FOLD))
    p.add_argument("--out",default=str(E4/"native_review_packets"))
    p.add_argument("--limit",type=int,default=None)
    p.add_argument("--selftest",action="store_true")
    a=p.parse_args()
    if a.selftest:selftest()
    else:review_packets(a.crosswalk,a.foldout,a.out,a.limit)
