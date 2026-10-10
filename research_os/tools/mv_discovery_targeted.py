#!/usr/bin/env python3
"""Independent native-source geometry follow-up for EXP004 ring candidates.
An exploratory review/triage pipeline, NEVER a semantic same-object classifier.
"""
from __future__ import annotations
import argparse
import itertools
import json
import math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
from exp003_yale_visual_inventory import fetch_image
from exp004_radial_rosette_comparison import registration

ROOT=Path(__file__).resolve().parents[1]
E2=ROOT/"experiments"/"EXP-2026-002"
E4=ROOT/"experiments"/"EXP-2026-004"

def count_baseline(a,b):
    # Count-only similarity CANNOT imply shared depicted object.
    keys=("radial_line_peak_proposals","annular_ring_peak_proposals")
    return round(sum((1 - abs(a[k]-b[k])/max(1,a[k],b[k])) for k in keys)/2,5)

def prepare_native_crop(bgr, center, radius, size=720):
    h,w=bgr.shape[:2]
    cx,cy=center[0]*w,center[1]*h
    rr=radius*min(h,w)*1.10
    x0=max(0,int(cx-rr)); x1=min(w,int(cx+rr))
    y0=max(0,int(cy-rr)); y1=min(h,int(cy+rr))
    if x1-x0<24 or y1-y0<24:
        return None,{"clipped":True,"valid":False}
    clip = (cx-rr<0 or cy-rr<0 or cx+rr>w or cy+rr>h)
    im=bgr[y0:y1,x0:x1]
    scale=min(1.0,size/max(im.shape[:2]))
    if scale<1:
        im=cv2.resize(im,(max(1,int(im.shape[1]*scale)),max(1,int(im.shape[0]*scale))),interpolation=cv2.INTER_AREA)
    return im,{"clipped":bool(clip),"valid":True,"original_bbox_xyxy_px":[x0,y0,x1,y1],
               "crop_size_px":[int(im.shape[1]),int(im.shape[0])]}

def orb_features(im):
    if im is None:return [],None
    gray=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    # Equalization makes detector less dependent on green / ochre RGB hue.
    edge=cv2.Canny(cv2.createCLAHE(clipLimit=2.0,tileGridSize=(8,8)).apply(gray),45,130)
    orb=cv2.ORB_create(nfeatures=700,fastThreshold=7)
    return orb.detectAndCompute(edge,None)

def orb_geometric_match(fa,fb):
    ka,da=fa; kb,db=fb
    if da is None or db is None or len(ka)<4 or len(kb)<4:
        return {"orb_keypoints_a":len(ka),"orb_keypoints_b":len(kb),"mutual_matches":0,
                "rigid_ransac_inliers":0,"rigid_inlier_fraction":0., "evidence":"INSUFFICIENT_KEYPOINTS"}
    matcher=cv2.BFMatcher(cv2.NORM_HAMMING)
    good=[]
    for match in matcher.knnMatch(da,db,k=2):
        if len(match)==2 and match[0].distance<.72*match[1].distance:
            good.append(match[0])
    if len(good)<4:
        return {"orb_keypoints_a":len(ka),"orb_keypoints_b":len(kb),"mutual_matches":len(good),
                "rigid_ransac_inliers":0,"rigid_inlier_fraction":0., "evidence":"NO_RIGID_FIT"}
    pa=np.float32([ka[m.queryIdx].pt for m in good]).reshape(-1,1,2)
    pb=np.float32([kb[m.trainIdx].pt for m in good]).reshape(-1,1,2)
    mat,inliers=cv2.estimateAffinePartial2D(pa,pb,method=cv2.RANSAC,
                                           ransacReprojThreshold=5.0,maxIters=2000)
    n=int(inliers.sum()) if inliers is not None else 0
    return {"orb_keypoints_a":len(ka),"orb_keypoints_b":len(kb),"mutual_matches":len(good),
            "rigid_ransac_inliers":n,
            "rigid_inlier_fraction":round(n/max(1,len(good)),4),
            "evidence":"GEOMETRIC_CANDIDATE_NOT_IDENTITY" if n>=5 else "WEAK_OR_NO_GEOMETRIC_SUPPORT"}

def compatible_groups(a,b):
    return a["canvas_oid"]!=b["canvas_oid"] and not (
        set(a.get("physical_groups",[])) & set(b.get("physical_groups",[]))
    )

def section_of(x,folio_to_section):
    return folio_to_section.get(x["folio"],"UNKNOWN")

def rank_screen(a,b,orb):
    reg=registration(a,b)
    cb=count_baseline(a,b)
    # No double counting same edge-derived radial signals as independent channels.
    return reg,cb,{"orb_ransac_at_least_5":orb["rigid_ransac_inliers"]>=5,
                   "ring_only_exploratory":reg["score_exploratory"],
                   "count_only_exploratory":cb}

def as_panel(im, width=360, height=290):
    if im is None:return Image.new("RGB",(width,height),"#ddd")
    out=Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB))
    out.thumbnail((width,height))
    bg=Image.new("RGB",(width,height),"white")
    bg.paste(out,((width-out.width)//2,(height-out.height)//2))
    return bg

def make_sheet(pairs, regions, image_crops, path, n=16):
    top=pairs[:n]
    w=790; rowh=365
    sheet=Image.new("RGB",(w,55+rowh*len(top)),(247,245,241))
    pen=ImageDraw.Draw(sheet)
    pen.text((14,13),"SOURCE-NATIVE CROPS: REVIEW PROPOSALS ONLY, NOT THE SAME OBJECT",(15,15,15))
    for i,p in enumerate(top):
        y=55+i*rowh
        a,b=regions[p["id_a"]],regions[p["id_b"]]
        pen.text((10,y+4),f'{i+1}. {p["folio_a"]}  <>  {p["folio_b"]} | radial {p["radial_score"]:.3f} | rigid inliers {p["rigid_inliers"]}',(25,25,25))
        pen.text((10,y+23),f'color-only/text-only: NOT_ASSESSED | source JPEG SHA verified | MV2+ NOT_ESTABLISHED',(70,70,70))
        sheet.paste(as_panel(image_crops[p["id_a"]]),(12,y+56))
        sheet.paste(as_panel(image_crops[p["id_b"]]),(407,y+56))
        pen.text((14,y+346),p["id_a"]+" vs "+p["id_b"],(66,66,66))
    path.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(path)
    return len(top)

def build(radial_json,crosswalk,out_dir):
    evidence=json.loads(Path(radial_json).read_text(encoding="utf8"))
    src=json.loads(Path(crosswalk).read_text(encoding="utf8"))
    if evidence.get("scientific_status")!="EXPLORATORY_NOT_CONFIRMED":
        raise ValueError("Unexpected radial evidence status")
    rows=evidence["regions"]
    if len(rows)<20:raise ValueError("Insufficient original radial candidate universe")
    ledger={str(x["canvas_oid"]):x for x in src["archive_files"]}
    photographs={}
    feature_cache={}
    crop_cache={}
    detail_cache={}
    for c in rows:
        oid=str(c["canvas_oid"])
        if oid not in ledger:raise ValueError("Missing source photo")
        if c["jpeg_sha256"]!=ledger[oid]["imported_reported_sha256"]:
            raise ValueError("Mismatched source SHA identity")
        if oid not in photographs:
            photographs[oid]=fetch_image(ledger[oid]) # recalculates raw-JPEG SHA256
        im,details=prepare_native_crop(photographs[oid],c["center_normalized"],c["radius_frac_min_axis"])
        k=c["candidate_id"]
        crop_cache[k]=im
        detail_cache[k]=details
        feature_cache[k]=orb_features(im)
    physical_pairs=[]
    for a,b in itertools.combinations(rows,2):
        if not compatible_groups(a,b):continue
        if not detail_cache[a["candidate_id"]]["valid"] or not detail_cache[b["candidate_id"]]["valid"]:continue
        ids=(a["candidate_id"],b["candidate_id"])
        orb=orb_geometric_match(feature_cache[ids[0]],feature_cache[ids[1]])
        reg,cb,_=rank_screen(a,b,orb)
        physical_pairs.append({
            "id_a":ids[0],"id_b":ids[1],
            "folio_a":a["folio"],"folio_b":b["folio"],
            "groups_a":a["physical_groups"],"groups_b":b["physical_groups"],
            "radial_score":reg["score_exploratory"],"angle_corr":reg["angular_correlation"],
            "ring_corr":reg["ring_correlation"],"count_only_score":cb,
            "reflection_required_by_radial_alignment":reg["mirror"],
            "view_shift_5_degree_bins":reg["view_shift_in_5degree_bins"],
            "radial_rich":reg["rich_radial_evidence"],
            "rigid_inliers":orb["rigid_ransac_inliers"],
            "orb":orb,
            "bbox_a":detail_cache[ids[0]],"bbox_b":detail_cache[ids[1]],
            "color_only_control":"NOT_ASSESSED_SOURCE_NOT_ANNOTATED",
            "text_only_control":"NOT_ASSESSED_SOURCE_NOT_REGISTERED",
            "count_only_control":"COMPUTED_DESCRIPTIVE_BASELINE_NOT_NULL_SIGNIFICANCE",
            "outline_only_control":"COMPUTED_RADIAL_PROFILE_NOT_PROOF",
            "faces_women_towers_stars":"UNKNOWN_NOT_ANNOTATED",
            "semantic_identity":"NOT_ESTABLISHED",
            "MV":"MV0_OR_MV1_REVIEW_ONLY",
        })
    if not physical_pairs:raise RuntimeError("No physically independent pairs")
    # Descriptive ranks in the same exploratory search universe: not p-values.
    vals=np.array([x["radial_score"] for x in physical_pairs],dtype=float)
    for p in physical_pairs:
        p["fraction_background_pairs_at_least_radial"]=round(float(np.mean(vals>=p["radial_score"])),4)
        p["focused_67v_85_86"]=("67v" in (p["folio_a"],p["folio_b"])
                              and ("85" in p["folio_a"] or "85" in p["folio_b"]
                                   or "86" in p["folio_a"] or "86" in p["folio_b"]))
        p["potential_leakage"]="FORBID_IDENTICAL_PHYSICAL_GROUPS; NO_HELDOUT_DATA_USED"
    physical_pairs.sort(key=lambda p:(
        not p["focused_67v_85_86"],not p["radial_rich"],
        -p["rigid_inliers"],-p["radial_score"],p["id_a"],p["id_b"]))
    d={x["candidate_id"]:x for x in rows}
    out_dir=Path(out_dir);out_dir.mkdir(parents=True,exist_ok=True)
    board=out_dir/"targeted_source_native_contact_sheet.png"
    shown=make_sheet(physical_pairs,d,crop_cache,board,n=16)
    output={
        "schema":"voynich-mv-discovery-radial-native-evidence-v1",
        "scientific_status":"EXPLORATORY_NOT_CONFIRMED",
        "experiment":"MV-2026-10-09 targeted follow-on",
        "photo_sources_sha256_recomputed_in_this_job":True,
        "source_photos":len(photographs),
        "candidate_radial_shapes":len(rows),
        "independent_physical_group_pairs":len(physical_pairs),
        "focused_67v_foldout_comparisons":sum(x["focused_67v_85_86"] for x in physical_pairs),
        "count_only_control":"DESCRIPTIVE",
        "outline_only_control":"DESCRIPTIVE",
        "color_only_control":"NOT_ASSESSED",
        "text_only_control":"NOT_ASSESSED",
        "human_annotation":"NOT_RUN",
        "within_between_section_control":"NOT_ASSESSED_PENDING_SEPARATE_SOURCE_REGISTRATION",
        "independent_validation":"NOT_RUN",
        "claimed_mv3":0,"claimed_mv4":0,
        "pair_review_board":str(board),
        "board_pairs":shown,
        "top_pairs":physical_pairs[:40],
        "all_pair_counts":{"with_native_rigid_ge5":sum(p["rigid_inliers"]>=5 for p in physical_pairs),
                           "rich_radial":sum(p["radial_rich"] for p in physical_pairs)},
        "warnings":[
          "ORB rigid inlier support and radial profile match are not semantic identity or different perspective evidence.",
          "The screening pool was selected by a previous Hough circle detector; rank fractions are selection biased, not p-values.",
          "Count and outline channels are not independent as both are computed from the same grayscale edges.",
          "Reflected transforms have not been independently physically validated; ring/peak counts not historical object counts.",
          "Do not promote above MV1 without human semantic masks and four adequate isolated null controls."
        ]
    }
    (out_dir/"targeted_pairs.json").write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("MV_DISCOVERY_NATIVE", "PHOTOS",len(photographs),"REGIONS",len(rows),
          "PAIRS",len(physical_pairs),"FOCUS",output["focused_67v_foldout_comparisons"],
          "RIGID_GE5",output["all_pair_counts"]["with_native_rigid_ge5"],
          "BOARD",shown,"STATUS",output["scientific_status"],flush=True)
    for p in physical_pairs[:12]:
        print("MV_REVIEW",p["folio_a"],"<=>",p["folio_b"],"RADIAL",
              p["radial_score"],"INLIERS",p["rigid_inliers"],"PRIOR_ONLY",flush=True)
    return output

def selftest():
    a={"radial_line_peak_proposals":6,"annular_ring_peak_proposals":3}
    b={"radial_line_peak_proposals":6,"annular_ring_peak_proposals":3}
    c={"radial_line_peak_proposals":1,"annular_ring_peak_proposals":0}
    assert count_baseline(a,b)==1.0 and count_baseline(a,c)<.4
    assert compatible_groups({"canvas_oid":"a","physical_groups":["QI-B1"]},
                              {"canvas_oid":"b","physical_groups":["QN-B1"]})
    assert not compatible_groups({"canvas_oid":"a","physical_groups":["QI-B1"]},
                                 {"canvas_oid":"b","physical_groups":["QI-B1"]})
    im=np.zeros((300,450,3),dtype=np.uint8)
    crop,dt=prepare_native_crop(im,[.5,.5],.15)
    assert crop is not None and dt["valid"] and not dt["clipped"]
    assert orb_geometric_match(([],None),([],None))["rigid_ransac_inliers"]==0
    print("MV_DISCOVERY_SELFTEST_PASS COUNT_ONLY PHYSICAL_GROUP CROPS ORB_FALLBACK",flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--radial",default=str(E4/"foldout_radial_matches_v1.json"))
    p.add_argument("--crosswalk",default=str(E2/"yale_archived_jpeg_provenance_crosswalk_2026-10-09.json"))
    p.add_argument("--out",default=str(E4/"mv_discovery_followup"))
    p.add_argument("--selftest",action="store_true")
    a=p.parse_args()
    if a.selftest:selftest()
    else:build(a.radial,a.crosswalk,a.out)
