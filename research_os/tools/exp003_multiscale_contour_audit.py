#!/usr/bin/env python3
"""EXP-2026-003: Scale-invariant silhouette candidate search in SHA-verified Yale MS408 photographs.

Finds photographic *shape similarities*, not shared meaning, structure or 3D depth.
An exploratory screen, with no held-out claim and no numerical scientific PASS.
"""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

import cv2
import numpy as np

from exp003_yale_visual_inventory import fetch_image, resize_photo, classify_pixel_masks

ROOT=Path(__file__).resolve().parents[1]
EXPERIMENT=ROOT/"experiments"/"EXP-2026-003"
LEDGER=ROOT/"experiments"/"EXP-2026-002"/"yale_archived_jpeg_provenance_crosswalk_2026-10-09.json"
LABELS=["9r","10r","75v","76r","85v and 86r (foldout)","94v and 95r"]
COLORS=["zielony","niebieski","czerwony","żółto-ochrowy"]
BASE_SIZE=112
SHAPE_SIZE=94

def normalize(binary):
    hh,ww=binary.shape
    factor=SHAPE_SIZE/max(ww,hh)
    new_w=max(1,int(round(ww*factor)))
    new_h=max(1,int(round(hh*factor)))
    small=cv2.resize(binary,(new_w,new_h),interpolation=cv2.INTER_NEAREST)
    dst=np.zeros((BASE_SIZE,BASE_SIZE),dtype=np.uint8)
    top=(BASE_SIZE-new_h)//2;left=(BASE_SIZE-new_w)//2
    dst[top:top+new_h,left:left+new_w]=small
    return dst

def iou(a,b):
    aa=a>0;bb=b>0
    return float(np.count_nonzero(aa & bb)/max(1,np.count_nonzero(aa | bb)))

def compare(a,b):
    q=a["normalized"];t=b["normalized"]
    candidates=[]
    for angle in (0,90,180,270):
        rotated=np.rot90(t,angle//90)
        for mirror in (False,True):
            translated=np.fliplr(rotated) if mirror else rotated
            s=iou(q,translated)
            candidates.append((s,angle,mirror))
    hit=max(candidates,key=lambda x:x[0])
    hu=float(cv2.matchShapes(a["contour"],b["contour"],cv2.CONTOURS_MATCH_I1,0.))
    factor=a["long_axis_pixels"]/b["long_axis_pixels"]
    scaled_aspect=b["aspect"] if hit[1]%180==0 else 1/b["aspect"]
    aspect_error=abs(math.log(a["aspect"]/scaled_aspect))
    # Our mask metric always keeps its original aspect ratio within 112x112.
    # Strong convexity/complexity mismatch also reduces score.
    score=0.84*hit[0]+0.16*math.exp(-min(12,max(0,hu)))
    score-=0.065*min(3,abs(a["solidity"]-b["solidity"])*3.5)
    if hit[2]:score-=0.025 # mirrored evidence less strong historically
    return {"shape_score":round(max(0,score),4),
            "normalized_mask_iou":round(hit[0],4),
            "hu_contour_distance":round(hu,5),
            "orientation_rotation_deg":int(hit[1]),
            "mirror":bool(hit[2]),
            "scale_factor_source_a_over_source_b_pixels":round(factor,4),
            "source_a_width_height_ratio":round(a["aspect"],3),
            "source_b_width_height_ratio":round(b["aspect"],3),
            "post_rotation_log_aspect_error":round(aspect_error,4),
            "silhouette_solidity_delta":round(abs(a["solidity"]-b["solidity"]),3)}

def extract(source):
    im=source["pixels"]
    hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
    masks,_=classify_pixel_masks(im)
    rois=[]
    for name in COLORS:
        bit=masks[name].astype(np.uint8)
        bit=cv2.morphologyEx(bit,cv2.MORPH_OPEN,np.ones((3,3),dtype=np.uint8))
        # A tiny amount of gap closure within paint is allowed. Do not join distant parts.
        bit=cv2.morphologyEx(bit,cv2.MORPH_CLOSE,np.ones((3,3),dtype=np.uint8))
        conts,_=cv2.findContours(bit,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        conts=sorted(conts,key=cv2.contourArea,reverse=True)
        count=0
        for contour in conts:
            ar=cv2.contourArea(contour)
            x,y,w,h=cv2.boundingRect(contour)
            if (w<17 or h<17 or ar<150 or ar>bit.size*.07
                    or max(w/h,h/w)>8 or w*h>bit.size*.22):
                continue
            hull=cv2.convexHull(contour)
            hull_area=cv2.contourArea(hull)
            if hull_area<1:continue
            solidity=float(ar/hull_area)
            # Suppress near-convex ovals and blob artifacts in primary ranking.
            # They remain documented in audit counters, not considered discoveries.
            if solidity >.90: continue
            roi=np.zeros((h,w),np.uint8)
            local=contour.copy()
            local[:,0,0]-=x;local[:,0,1]-=y
            cv2.drawContours(roi,[local],-1,1,-1)
            mask=normalize(roi)
            rois.append({
                "id":f'{source["label"]}:{name}:{count}',"folio_label":source["label"],
                "canvas_oid":source["canvas_oid"],"pigment_appearance_bin":name,
                "bbox_source_working_xywh":[int(x),int(y),int(w),int(h)],
                "bbox_normalized_xywh":[round(x/im.shape[1],5),round(y/im.shape[0],5),
                                         round(w/im.shape[1],5),round(h/im.shape[0],5)],
                "working_shape_px":[int(im.shape[1]),int(im.shape[0])],
                "long_axis_pixels":int(max(w,h)), "aspect":float(w/h),
                "solidity":solidity,"contour":local,"normalized":mask,
                "area_pixels":round(ar,2),
                "source_pixels":im[y:y+h,x:x+w],
            })
            count+=1
            if count>=55:break
    return rois

def run(out,preview):
    archive=json.loads(LEDGER.read_text(encoding="utf-8"))
    source_entries={}
    for e in archive["archive_files"]:
        if e["yale_label"] in LABELS:source_entries[e["yale_label"]]=e
    if set(source_entries)!=set(LABELS):
        raise ValueError("One of six planned sources is absent in archival manifest.")
    sources=[];all_regions=[]
    for label in LABELS:
        entry=source_entries[label]
        raw=fetch_image(entry) # hash-validated Yale archive JPEG bytes
        h,w=raw.shape[:2]
        # global image size standardized for extraction; native widths recorded
        scale=min(1.,1600./max(h,w))
        work=cv2.resize(raw,(round(w*scale),round(h*scale)),
                        interpolation=cv2.INTER_AREA) if scale<1 else raw
        source={"label":label,"canvas_oid":entry["canvas_oid"],"pixels":work}
        regions=extract(source)
        sources.append({"label":label,"canvas_oid":entry["canvas_oid"],
                        "verified_sha256":entry["imported_reported_sha256"],
                        "archive_file":entry["path"],
                        "native_dimensions":[w,h],
                        "working_dimensions":[work.shape[1],work.shape[0]],
                        "irregular_color_components":len(regions)})
        all_regions.extend(regions)
        print("SOURCE",label,"SHA_VERIFIED",entry["imported_reported_sha256"][:16],
              "COMPLEX_ROIS",len(regions),flush=True)
    hits=[];counter=0
    for a,b in itertools.combinations(all_regions,2):
        if a["folio_label"]==b["folio_label"]:continue
        if a["pigment_appearance_bin"]!=b["pigment_appearance_bin"]:continue
        if a["canvas_oid"]==b["canvas_oid"]:continue
        metrics=compare(a,b)
        counter+=1
        hits.append({"id_a":a["id"],"id_b":b["id"],"color_bin":a["pigment_appearance_bin"],
                     **metrics})
    hits.sort(key=lambda p:p["shape_score"],reverse=True)
    def eligible(p):
        # interesting-scale subset, not significance threshold
        r=p["scale_factor_source_a_over_source_b_pixels"]
        return (r>=1.65 or r<=1/1.65) and p["normalized_mask_iou"]>=.50
    wide=[p for p in hits if eligible(p)]
    distinct=[];used=set()
    for p in wide:
        if p["id_a"] in used or p["id_b"] in used:continue
        distinct.append(p)
        used.add(p["id_a"]);used.add(p["id_b"])
        if len(distinct)>=20:break
    # Calibrate against ALL candidate cross-folio pairs, with no inferential p-value.
    scores=sorted(p["shape_score"] for p in hits)
    def perc(q):
        return round(float(np.percentile(scores,q)),4) if scores else None
    report={
      "schema":"exp003-scale-normalized-source-color-contours-v1",
      "scientific_status":"EXPLORATORY_NON_CONFIRMATORY",
      "tested_hypothesis":"Do irregular pigment-colored image regions recur as similar normalized shapes at different digital pixel sizes?",
      "negative_control":"Cross-folio color-bin-matched shape candidates; distribution of ALL compared pairs; not an independent held-out null.",
      "strict_semantic_verdict":"INCONCLUSIVE_NOT_RUN",
      "source_branch":"import-voynich-yale-scans-2026-07-23",
      "provenance_crosswalk_sha256":hashlib.sha256(LEDGER.read_bytes()).hexdigest(),
      "sources":sources,
      "regions":[{"id":r["id"],"canvas_oid":r["canvas_oid"],
                  "folio_label":r["folio_label"],
                  "color_bin":r["pigment_appearance_bin"],
                  "bbox_source_working_xywh":r["bbox_source_working_xywh"],
                  "bbox_normalized_xywh":r["bbox_normalized_xywh"],
                  "working_shape_px":r["working_shape_px"],
                  "length_pixels":r["long_axis_pixels"],
                  "width_height_ratio":round(r["aspect"],4),
                  "solidity":round(r["solidity"],4),
                  "area_pixels":r["area_pixels"]} for r in all_regions],
      "region_count":len(all_regions),
      "compared_pairs":counter,
      "scale_threshold_1_65x_qualifying_pair_count":len(wide),
      "score_distribution_all_pairs":{"p50":perc(50),"p90":perc(90),"p95":perc(95),"p99":perc(99)},
      "top_pairs_all_scales":hits[:25],"top_distinct_scale_change_pairs":distinct,
      "limits":[
        "Pixel magnification between archival canvases is NOT historic object size or manuscript millimetres.",
        "Shape contours from HSV/Lab images are digital appearance only, without validated semantic segmentation.",
        "Contour IoU after scaling/90-degree rotation and mirroring is NOT evidence of identical botanical species, tower, water system or 3D object.",
        "Images selected after reviewing the user's screenshots are not an independent test set.",
        "Simplified near-convex blobs removed from main ranking (solidity>0.90), but remaining repeated strokes can still be generic style.",
        "Images are downsampled for CV (1600px max dimension); original JPEG SHA verified before processing.",
        "Perceptual edge/shape similarity excludes text relationship, historical direction, semantic pigment role and 2.5D depth."
      ]
    }
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    # Proof sheet with actual source-image crops, not synthetic illustrations
    if distinct:
        from PIL import Image,ImageDraw
        lookup={r["id"]:r for r in all_regions}
        panel=Image.new("RGB",(1030,len(distinct)*157+55),"white")
        draw=ImageDraw.Draw(panel)
        draw.text((12,12),"EXP003 source-verified SHAPE candidates | after scale-normalization | NOT confirmed",
                  fill=(20,20,20))
        for k,p in enumerate(distinct):
            a,b=lookup[p["id_a"]],lookup[p["id_b"]]
            y=47+157*k
            for x,roi in [(14,a),(515,b)]:
                cropped=cv2.cvtColor(roi["source_pixels"],cv2.COLOR_BGR2RGB)
                pic=Image.fromarray(cropped);pic.thumbnail((195,98))
                panel.paste(pic,(x,y+18))
                mask=Image.fromarray(roi["normalized"]*255).convert("RGB")
                panel.paste(mask,(x+211,y+18))
                draw.text((x,y),roi["id"],fill=(22,22,22))
            draw.text((14,y+122),f"score={p['shape_score']} IoU={p['normalized_mask_iou']} "
                      f"scale={p['scale_factor_source_a_over_source_b_pixels']}x "
                      f"rotate={p['orientation_rotation_deg']} mirror={p['mirror']}",
                      fill=(20,20,20))
        pp=Path(preview);pp.parent.mkdir(parents=True,exist_ok=True)
        panel.save(pp)
        print("PREVIEW",pp,flush=True)
    print("COMPLETE","regions",len(all_regions),"pairs",counter,"largescale",len(wide),
          "distinctx",len(distinct),"distribution",report["score_distribution_all_pairs"],flush=True)
    for p in distinct[:10]:
        print("CANDIDATE",p["id_a"],p["id_b"],p["shape_score"],
              p["scale_factor_source_a_over_source_b_pixels"],flush=True)

def selftest():
    base=np.zeros((45,75),dtype=np.uint8)
    points=np.array([[1,17],[25,11],[32,0],[43,16],[72,3],[61,32],[46,38],[28,35],[0,44]],np.int32)
    cv2.fillPoly(base,[points],1)
    larger=cv2.resize(base,(225,135),interpolation=cv2.INTER_NEAREST)
    a={"normalized":normalize(base),"contour":cv2.findContours(base,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0][0],
       "long_axis_pixels":75,"aspect":75/45,"solidity":.75}
    b={"normalized":normalize(larger),"contour":cv2.findContours(larger,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0][0],
       "long_axis_pixels":225,"aspect":225/135,"solidity":.75}
    m=compare(a,b)
    assert abs(m["scale_factor_source_a_over_source_b_pixels"]-1/3)<.0005,m
    assert m["normalized_mask_iou"]>.89,m
    assert m["shape_score"]>.75,m
    assert len(normalize(base).shape)==2
    print("SELFTEST PASS: synthetic shape x3 gives scale ratio 0.333 and strong scale-normalized IoU",m,flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",default=str(EXPERIMENT/"multiscale_shape_candidates_2026-10-09.json"))
    p.add_argument("--preview",default=str(EXPERIMENT/"multiscale_shape_contact_sheet_2026-10-09.png"))
    p.add_argument("--selftest",action="store_true")
    args=p.parse_args()
    if args.selftest:selftest()
    else:run(args.output,args.preview)
