#!/usr/bin/env python3
"""EXP004 native-photo side-by-side shortlist, manual evaluation only.

Each panel uses the original JPEG archived source whose SHA256 is verified.
Comparison still cannot establish same object, pigment or perspective.
"""
import argparse
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw
from exp003_yale_visual_inventory import fetch_image

ROOT=Path(__file__).resolve().parents[1]
E2=ROOT/"experiments"/"EXP-2026-002"
E4=ROOT/"experiments"/"EXP-2026-004"

def extract_region(bgr,roi_box,padding=.32):
    h,w=bgr.shape[:2]
    x,y,bw,bh=[float(v) for v in roi_box]
    px=bw*padding;py=bh*padding
    l=max(0,int((x-px)*w));t=max(0,int((y-py)*h))
    r=min(w,int((x+bw+px)*w));b=min(h,int((y+bh+py)*h))
    if r-l<4 or b-t<4:raise ValueError("Small or invalid bounding region")
    return bgr[t:b,l:r].copy()

def paste_fit(canvas,rgb,x,y,width=260,height=190):
    picture=Image.fromarray(rgb)
    picture.thumbnail((width,height))
    canvas.paste(picture,(x+(width-picture.width)//2,y+(height-picture.height)//2))
    return picture.size

def build(data_path,ledger_path,out,limit=12):
    data=json.loads(Path(data_path).read_text(encoding="utf-8"))
    ledger=json.loads(Path(ledger_path).read_text(encoding="utf-8"))
    if data.get("schema")!="voynich-exp004/multifolio-object-candidates-v1":
        raise ValueError("Source atlas schema mismatch")
    candidate=data["ranked_proposed_shape_correspondences"][:limit]
    rois={r["id"]:r for r in data["region_proposals"]}
    entries={str(e["canvas_oid"]):e for e in ledger["archive_files"]}
    photos={}
    for m in candidate:
        for oid in [m["canvas_a"],m["canvas_b"]]:
            if oid in photos:continue
            photos[oid]=fetch_image(entries[oid])   # native jpeg SHA256 checked
            print("PHOTO",oid,"SHA256_VERIFIED",entries[oid]["imported_reported_sha256"][:18],flush=True)
    width=740;cell_h=260
    board=Image.new("RGB",(width,65+cell_h*len(candidate)),(246,244,238))
    draw=ImageDraw.Draw(board)
    draw.text((12,12),"EXP004 SOURCE NATIVE CROPS - CANDIDATE ONLY; NOT SAME OBJECT",(24,24,24))
    draw.text((12,34),"Each image crop from original Yale archived SHA-verified JPEG. Score = digital dHash.",(50,50,50))
    for n,m in enumerate(candidate):
        y=65+n*cell_h
        a=rois[m["roi_a"]];b=rois[m["roi_b"]]
        pixa=extract_region(photos[a["canvas_oid"]],a["source_bbox_xywh_norm"])
        pixb=extract_region(photos[b["canvas_oid"]],b["source_bbox_xywh_norm"])
        ra=cv2.cvtColor(pixa,cv2.COLOR_BGR2RGB);rb=cv2.cvtColor(pixb,cv2.COLOR_BGR2RGB)
        draw.rectangle((8,y+8,width-9,y+cell_h-8),outline=(189,183,174))
        draw.text((22,y+14),str(n+1)+". "+str(m["folio_a"])+"     <-->     "+str(m["folio_b"])+
                  "  hamming="+str(m["dhash_hamming_64"])+
                  "  appearance="+str(m["color_appearance_label"]),(35,35,35))
        paste_fit(board,ra,55,y+42,260,180)
        paste_fit(board,rb,423,y+42,260,180)
        draw.text((50,y+230),str(m["roi_a"])[:45],(58,58,58))
        draw.text((423,y+230),str(m["roi_b"])[:45],(58,58,58))
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    board.save(out,optimize=True)
    print("EXP004_CONTACT_SHEET",out,"PAIRS",len(candidate),"CANVASES",len(photos),flush=True)

def selftest():
    image=np.zeros((200,150,3),np.uint8)
    crop=extract_region(image,[.2,.2,.2,.3])
    assert crop.shape[0]>0 and crop.shape[1]>0
    pic=Image.new("RGB",(400,300),"white")
    paste_fit(pic,cv2.cvtColor(crop,cv2.COLOR_BGR2RGB),10,10)
    print("EXP004_CONTACT_SHEET_SELFTEST_PASS native bbox crop + thumbnail")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--atlas",default=str(E4/"multifolio_object_atlas_v1.json"))
    p.add_argument("--crosswalk",default=str(E2/"yale_archived_jpeg_provenance_crosswalk_2026-10-09.json"))
    p.add_argument("--out",default=str(E4/"paired_native_image_review_board.png"))
    p.add_argument("--limit",type=int,default=12)
    p.add_argument("--selftest",action="store_true")
    args=p.parse_args()
    if args.selftest:selftest()
    else:build(args.atlas,args.crosswalk,args.out,args.limit)
