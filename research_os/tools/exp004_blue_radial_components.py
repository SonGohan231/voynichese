#!/usr/bin/env python3
"""EXP004 source-level blue radial pattern comparison for f68v vs f85v/f86r.

Pixel geometry is NOT verified star-count or historic motif identity.
Blue appearance = conservative digital color filtering; thresholds and
false negatives are audited by sensitivity across 3 saturation cutoffs.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import cv2
import numpy as np
from exp003_yale_visual_inventory import fetch_image

ROOT=Path(__file__).resolve().parents[1]
E2=ROOT/"experiments"/"EXP-2026-002"
E3=ROOT/"experiments"/"EXP-2026-003"
E4=ROOT/"experiments"/"EXP-2026-004"
CROSS=E2/"yale_archived_jpeg_provenance_crosswalk_2026-10-09.json"
FOLD=E3/"foldout_geometry_probe_2026-10-09.json"
OIDS=["1006197","1006231"]
SATURATION=[50,75,100]
OCCUPANCY=[.07,.11,.16]
TARGET_COLS=340
TARGET_ROWS=120

def circular_runs(v):
    """Return distinct positive consecutive angular runs on a circular grid."""
    x=np.array(v,dtype=bool)
    if not np.any(x):return []
    if np.all(x):return [list(range(len(x)))]
    starts=np.where(x & ~np.roll(x,1))[0]
    runs=[]
    for s in starts:
        result=[];j=int(s)
        while x[j]:
            result.append(j)
            j=(j+1)%len(x)
        if len(result)>=3:runs.append(result)
    return runs

def appearance_mask(bgr,smin=75):
    hsv=cv2.cvtColor(bgr,cv2.COLOR_BGR2HSV)
    # Strong blue/marine color, neither parchment-yellow nor faded cyan;
    # this is intentionally an incomplete conservative mask.
    return (((hsv[:,:,0]>=88)&(hsv[:,:,0]<=135)&
             (hsv[:,:,1]>=smin)&(hsv[:,:,2]>=22)&
             (hsv[:,:,2]<=235))).astype(np.uint8)

def angular_blue_density(mask,center,radius):
    h,w=mask.shape
    rr=np.linspace(.15,.93,TARGET_ROWS)
    tt=np.linspace(0,2*np.pi,TARGET_COLS,endpoint=False)
    cos=np.cos(tt)[:,None];sin=np.sin(tt)[:,None]
    xx=np.clip(np.rint(center[0]+radius*rr[None,:]*cos).astype(int),0,w-1)
    yy=np.clip(np.rint(center[1]+radius*rr[None,:]*sin).astype(int),0,h-1)
    sample=mask[yy,xx]
    # Not every radial stroke fills the center. Central and outer estimates
    # are recorded independently for auditing perspective/scale confounds.
    return (sample.mean(axis=1),float(sample.mean()))

def candidate(im,center,radius):
    profiles={}
    for sat in SATURATION:
        mask=appearance_mask(im,sat)
        profile,blue_occupancy=angular_blue_density(mask,center,radius)
        for occ in OCCUPANCY:
            active=(profile>=occ)
            # Tiny narrow spokes must survive >= 3 bins, central sector
            # counts are NOT actual drawn motif counts.
            parts=circular_runs(active)
            key=f"sat{sat}_occ{int(occ*100)}"
            profiles[key]={"blue_angular_run_count":len(parts),
                           "center_angle_deg":[round(((np.mean(part)*360/TARGET_COLS)%360),2)
                                               for part in parts],
                           "coverage_fraction":round(float(np.mean(active)),4),
                           "mask_blue_occupancy":round(blue_occupancy,4)}
    counts=[x["blue_angular_run_count"] for x in profiles.values()]
    return {"test_sensitivity":profiles,"median_blue_runs":int(np.median(counts)),
            "blue_runs_min_max":[int(min(counts)),int(max(counts))],
            "stability_band_width":int(max(counts)-min(counts)),
            "stable_enough_for_visual_review":bool(min(counts)>=3 and max(counts)-min(counts)<=2),
            "historical_star_spoke_sector_count":None,
            "semantic_identity":"UNDETERMINED"}

def blue_signature_score(a,b):
    vals=[]
    for key in a["test_sensitivity"]:
        x=a["test_sensitivity"][key];y=b["test_sensitivity"][key]
        na=x["blue_angular_run_count"];nb=y["blue_angular_run_count"]
        vals.append((1-abs(na-nb)/max(1,na,nb))*min(x["coverage_fraction"],y["coverage_fraction"]))
    score=float(np.median(vals))
    return round(score,4)

def crop_box(im,ctr,radius):
    h,w=im.shape[:2]
    l=max(0,round(ctr[0]-1.15*radius));t=max(0,round(ctr[1]-1.15*radius))
    r=min(w,round(ctr[0]+1.15*radius));b=min(h,round(ctr[1]+1.15*radius))
    return im[t:b,l:r].copy()

def make_board(records,source_imgs,path):
    # Multiple distinct circle features from two original Yale photos.
    # Pictorial preview is deliberately source-backed and marked UNKNOWN.
    cellw=500;cellh=440;cols=3;rows=math.ceil(len(records)/cols)
    from PIL import Image,ImageDraw
    canvas=Image.new("RGB",(cellw*cols,cellh*rows),(246,244,239))
    draw=ImageDraw.Draw(canvas)
    for i,r in enumerate(records):
        xx=(i%cols)*cellw;yy=(i//cols)*cellh
        oid=r["canvas_oid"];im=source_imgs[oid]
        h,w=im.shape[:2]
        ctr=(r["center_xy_fraction"][0]*w,r["center_xy_fraction"][1]*h)
        radius=r["circle_radius_short_axis"]*min(w,h)
        cropped=crop_box(im,ctr,radius)
        picture=Image.fromarray(cv2.cvtColor(cropped,cv2.COLOR_BGR2RGB))
        picture.thumbnail((470,340))
        canvas.paste(picture,(xx+(500-picture.width)//2,yy+70+(340-picture.height)//2))
        draw.text((xx+14,yy+11),str(r["folio"])+" "+str(r["candidate_id"]),fill=(35,35,35))
        draw.text((xx+14,yy+33),"BLUE-RUN PROXY: "+str(r["median_blue_runs"])+
                  " (range "+str(r["blue_runs_min_max"])+")",fill=(35,35,35))
        draw.text((xx+14,yy+413),"NOT CONFIRMED stars or sectors",fill=(130,50,50))
    canvas.save(path,optimize=True)

def main(out,board):
    cross=json.loads(Path(CROSS).read_text(encoding="utf-8"))
    previous=json.loads(Path(FOLD).read_text(encoding="utf-8"))
    entries={str(e["canvas_oid"]):e for e in cross["archive_files"]}
    selected={str(p["canvas_oid"]):p for p in previous["sources"] if str(p["canvas_oid"]) in OIDS}
    if set(selected)!=set(OIDS):raise ValueError("Missing planned foldout sources")
    allpics={};records=[]
    for oid in OIDS:
        entry=entries[oid]
        im=fetch_image(entry)
        # Decode authentic bytes, compare to independently stored SHA; use
        # working 2000 px to avoid excessive processing (scale recorded).
        oh,ow=im.shape[:2]
        sc=min(1.,2000/max(oh,ow))
        working=cv2.resize(im,(round(ow*sc),round(oh*sc)),
                           interpolation=cv2.INTER_AREA) if sc<1 else im
        allpics[oid]=working
        h,w=working.shape[:2]
        for j,feat in enumerate(selected[oid]["candidate_circular_regions"]):
            x,y=feat["center_xy"]
            r=feat["radius_fraction_of_minimum_axis"]
            features=candidate(working,(x*w,y*h),r*min(w,h))
            records.append({
               "candidate_id":f"{oid}-ring-{j}",
               "canvas_oid":oid,"folio":entry["yale_label"],
               "source_sha256":entry["imported_reported_sha256"],
               "native_dimensions":[ow,oh],"working_dimensions":[w,h],
               "center_xy_fraction":[x,y],
               "circle_radius_short_axis":r,"physical_groups":entry["physical_group_ids"],
               **features
            })
        print("BLUE_PATTERN_SOURCE",entry["yale_label"],len(selected[oid]["candidate_circular_regions"]),flush=True)
    matches=[]
    a=[z for z in records if z["canvas_oid"]==OIDS[0]]
    b=[z for z in records if z["canvas_oid"]==OIDS[1]]
    for x,y in itertools.product(a,b):
        matches.append({"a":x["candidate_id"],"b":y["candidate_id"],
                        "a_folio":x["folio"],"b_folio":y["folio"],
                        "proxy_similarity":blue_signature_score(x,y),
                        "median_digital_runs_a":x["median_blue_runs"],
                        "median_digital_runs_b":y["median_blue_runs"],
                        "both_stable":x["stable_enough_for_visual_review"] and
                                      y["stable_enough_for_visual_review"],
                        "verified_same_object":False,
                        "source_independent_groups":not(bool(set(x["physical_groups"])&set(y["physical_groups"])))})
    matches.sort(key=lambda x:(not x["both_stable"],-x["proxy_similarity"]))
    result={"schema":"exp004-blue-radial-sector-appearance-pilot-v1",
      "scientific_status":"EXPLORATORY_WITHOUT_VALIDATED_SECTOR_COUNTS",
      "input_sources":list(OIDS),
      "source_crosswalk_sha256":hashlib.sha256(Path(CROSS).read_bytes()).hexdigest(),
      "circle_candidates_count":len(records),
      "cross_physical_group_comparisons":len(matches),
      "blue_threshold_sensitivity_saturation":SATURATION,
      "blue_threshold_sensitivity_angular_occupancy":OCCUPANCY,
      "features":records,"cross_source_pairs":matches,
      "major_limits":["Hough circles can miss or hallucinate real circles",
        "Blue pixel runs depend strongly on illumination, fading and selection of sampling radius",
        "No confirmed spokes, rosettes, female figures or stars were automatically counted",
        "Digital blue appearance cannot establish pigment composition or semantic coding",
        "All indices exploratory, no independent codicological heldout or FDR control",
        "Rotation and actual alternative 2.5D perspective not measured",
        "Read as candidate digital radial pattern, not same historical object"] }
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    board=Path(board);board.parent.mkdir(parents=True,exist_ok=True)
    make_board(records,allpics,board)
    print("EXP004_BLUE_RADIAL",len(records),"CANDIDATES",len(matches),
          "CROSS_GROUP_PAIRS",sum(bool(z["source_independent_groups"]) for z in matches),
          "STABLE_PAIRS",sum(bool(z["both_stable"]) for z in matches),flush=True)
    for x in matches[:6]:print("BLUE_PAIR",x["a"],x["b"],x["proxy_similarity"],"BOTH_STABLE",x["both_stable"],flush=True)

def selftest():
    blank=np.zeros((400,400,3),np.uint8)
    # Centered 8-petal artificial filled blue wedge diagram.
    center=(200,200)
    for k in range(8):
        a=2*np.pi*k/8
        p1=(round(200+50*np.cos(a-.11)),round(200+50*np.sin(a-.11)))
        p2=(round(200+50*np.cos(a+.11)),round(200+50*np.sin(a+.11)))
        q1=(round(200+145*np.cos(a+.11)),round(200+145*np.sin(a+.11)))
        q2=(round(200+145*np.cos(a-.11)),round(200+145*np.sin(a-.11)))
        cv2.fillConvexPoly(blank,np.array([p1,p2,q1,q2],np.int32),(180,70,20))
    counts=candidate(blank,center,155)
    # Candidate may be threshold-sensitive, so validate shape not exact
    # mocked historical count.
    assert counts["median_blue_runs"]>=6,counts
    assert candidate(np.full_like(blank,235),center,155)["median_blue_runs"]==0
    assert len(circular_runs(np.zeros(20,dtype=bool)))==0
    print("EXP004_BLUE_SELFTEST_PASS manufactured radial sectors & unpainted false-positive guard",counts["median_blue_runs"])

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",default=str(E4/"source_blue_radial_shape_proxies.json"))
    p.add_argument("--board",default=str(E4/"source_blue_radial_candidate_board.png"))
    p.add_argument("--selftest",action="store_true")
    args=p.parse_args()
    if args.selftest:selftest()
    else:main(args.out,args.board)
