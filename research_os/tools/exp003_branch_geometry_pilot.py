#!/usr/bin/env python3
"""EXP003: exploratory structural comparison of original-scale normalized Yale contours.

NOT a botanical identification or confirmatory test. User-selected regions
are a discovery set; null percentile is descriptive after multiple selection.
"""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import cv2
import numpy as np
from skimage.morphology import skeletonize
from exp003_multiscale_contour_audit import (LEDGER, LABELS, normalize,
    extract, compare, SHAPE_SIZE)
from exp003_yale_visual_inventory import fetch_image

HERE=Path(__file__).resolve().parents[1]/"experiments"/"EXP-2026-003"
EXAMPLES=[
    ("10r:zielony:2", "94v and 95r:zielony:22"),
    ("10r:zielony:3", "94v and 95r:zielony:35"),
    ("10r:zielony:0", "94v and 95r:zielony:34"),
    ("9r:zielony:13", "94v and 95r:zielony:0"),
]
NEIGHBOR_KERNEL=np.ones((3,3), dtype=np.uint8)


def morphological_skeleton(mask):
    """Zhang-Suen style thinning: geometry probe only, not validated anatomy."""
    return skeletonize(mask>0).astype(np.uint8)


def signature(mask):
    binmask=(mask>0).astype(np.uint8)
    # Removing tiny isolated artifacts also changes thin genuine branches:
    # preserve the mask, quantify at one fixed scale, label uncertainty.
    sk=morphological_skeleton(binmask)
    degree=cv2.filter2D(sk,-1,NEIGHBOR_KERNEL)-sk
    endpoints=(sk>0)&(degree==1)
    jpix=((sk>0)&(degree>=3)).astype(np.uint8)
    # Cluster nearby junction pixels into centers.
    junctions=cv2.connectedComponents(cv2.dilate(jpix,NEIGHBOR_KERNEL,iterations=1))[0]-1 if jpix.any() else 0
    conts,_=cv2.findContours(binmask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    if not conts:
        return dict(endpoints=0,junctions=0,notches=0,aspect=0,radial_peaks=0,
                    radial_spacing=[],skeleton_pixels=0,area_fraction=0,solidity=0)
    contour=max(conts,key=cv2.contourArea)
    area=cv2.contourArea(contour)
    hull=cv2.convexHull(contour)
    solidity=area/max(1.,cv2.contourArea(hull))
    x,y,w,h=cv2.boundingRect(contour)
    hull_idx=cv2.convexHull(contour,returnPoints=False)
    # Archive scans may contain self-crossing pixel contours: in that case the
    # OpenCV hull index requirement is not satisfied. Mark as unmeasurable, not 0.
    defects=None
    defects_reliable=True
    if hull_idx is not None and len(hull_idx)>3 and len(contour)>4:
        try:
            defects=cv2.convexityDefects(contour,hull_idx)
        except cv2.error:
            defects_reliable=False
    dents=[]
    if defects is not None:
        for z in defects[:,0]:
            if z[3]/256>=0.045*max(w,h):
                dents.append(float(z[3]/256/max(w,h)))
    mom=cv2.moments(contour)
    cx=mom["m10"]/max(mom["m00"],1e-6);cy=mom["m01"]/max(mom["m00"],1e-6)
    pts=contour[:,0,:].astype(float)
    ang=np.mod(np.arctan2(pts[:,1]-cy,pts[:,0]-cx),2*np.pi)
    rad=np.sqrt((pts[:,0]-cx)**2+(pts[:,1]-cy)**2)
    bins=np.floor(ang*72/(2*np.pi)).astype(int)%72
    profile=np.zeros(72,dtype=float)
    for i,b in enumerate(bins):profile[b]=max(profile[b],rad[i])
    # Empty angular bins are interpolated circularly before peak counting.
    known=np.flatnonzero(profile>0)
    if len(known)>=2:
        xp=np.r_[known[-1]-72, known, known[0]+72]
        fp=np.r_[profile[known[-1]],profile[known],profile[known[0]]]
        profile=np.interp(np.arange(72),xp,fp)
    else:profile[:]=0
    p=(np.roll(profile,2)+2*np.roll(profile,1)+3*profile+
       2*np.roll(profile,-1)+np.roll(profile,-2))/9
    peak_idx=[i for i in range(72) if p[i]>p[(i-1)%72] and
              p[i]>=p[(i+1)%72] and p[i]-min(p[(i-4)%72],p[(i+4)%72])>0.055*max(1,p.max())]
    spacing=sorted(np.diff(np.r_[peak_idx,peak_idx[0]+72])/72) if peak_idx else []
    return {"endpoints":int(np.count_nonzero(endpoints)),
            "junctions":int(junctions),"notches":len(dents),
            "notch_depth_median":round(float(np.median(dents)),4) if dents else 0.,
            "notch_measurement_reliable":defects_reliable,
            "aspect":round(w/max(1,h),4),"radial_peaks":len(peak_idx),
            "radial_spacing":[round(float(x),4) for x in spacing],
            "skeleton_pixels":int(np.count_nonzero(sk)),
            "area_fraction":round(float(binmask.mean()),5),
            "solidity":round(float(solidity),5)}


def alignment_score(fa,fb,baseline):
    # Counts are not independent, and are not calibrated probabilities.
    count_keys=("endpoints","junctions","notches","radial_peaks")
    penalties={k:abs(fa[k]-fb[k]) for k in count_keys}
    ratio_a=max(1,fa["skeleton_pixels"])
    ratio_b=max(1,fb["skeleton_pixels"])
    branch_size_err=abs(math.log(ratio_a/ratio_b))
    a,b=fa["radial_spacing"],fb["radial_spacing"]
    if a and b:
        # Compare cyclically ordered gap multisets, with penalty for gap-count mismatch.
        m=min(len(a),len(b))
        gap_err=float(np.mean(np.abs(np.array(a[:m])-np.array(b[:m]))))
    else:gap_err=0.5 if bool(a)!=bool(b) else 0.
    loss=(0.15*min(3,penalties["endpoints"])+
          0.28*min(3,penalties["junctions"])+
          0.18*min(4,penalties["notches"])+
          0.12*min(4,penalties["radial_peaks"])+
          0.6*gap_err+0.08*min(3,branch_size_err))
    # Original IoU score dominates for simple silhouettes; explicitly
    # disqualify bland blobs from evidence of *complex branching*.
    is_simple=(min(fa["junctions"],fb["junctions"])<1 or
               min(fa["notches"],fb["notches"])<2 or
               not fa["notch_measurement_reliable"] or
               not fb["notch_measurement_reliable"])
    raw=round(float(0.4*baseline["shape_score"]+0.6*math.exp(-loss)),5)
    return {"structural_score_exploratory":raw,"different_branch_complexity":is_simple,
            "structural_comparison_eligible":not is_simple,
            "differences":penalties,"branch_skeleton_log_length_delta":round(branch_size_err,4),
            "radial_peak_gap_difference":round(gap_err,4)}


def run(out):
    ledger=json.loads(LEDGER.read_text(encoding="utf-8"))
    entries={e["yale_label"]:e for e in ledger["archive_files"] if e["yale_label"] in LABELS}
    if len(entries)!=len(LABELS):raise RuntimeError("Sources missing in ledger")
    regions=[];sources=[]
    for label in LABELS:
        e=entries[label]
        raw=fetch_image(e)  # Original bytes SHA-256 checked inside.
        h,w=raw.shape[:2]
        scale=min(1.,1600./max(h,w))
        im=cv2.resize(raw,(round(w*scale),round(h*scale)),interpolation=cv2.INTER_AREA) if scale<1 else raw
        rs=extract({"label":label,"canvas_oid":e["canvas_oid"],"pixels":im})
        for row in rs:row["signature"]=signature(row["normalized"])
        regions.extend(rs)
        sources.append({"label":label,"oid":e["canvas_oid"],"source_sha256":e["imported_reported_sha256"],"regions":len(rs)})
        print("SOURCE",label,len(rs),flush=True)
    rows=[]
    for a,b in itertools.combinations(regions,2):
        if a["canvas_oid"]==b["canvas_oid"] or a["pigment_appearance_bin"]!=b["pigment_appearance_bin"]:continue
        baseline=compare(a,b)
        structural=alignment_score(a["signature"],b["signature"],baseline)
        rows.append({"id_a":a["id"],"id_b":b["id"],"color":a["pigment_appearance_bin"],
                     "scale":baseline["scale_factor_source_a_over_source_b_pixels"],
                     "iou":baseline["normalized_mask_iou"],
                     "mirror":baseline["mirror"],"rotation":baseline["orientation_rotation_deg"],
                     **structural})
    rows.sort(key=lambda x:(not x["structural_comparison_eligible"],-x["structural_score_exploratory"]))
    pool=[r["structural_score_exploratory"] for r in rows if r["structural_comparison_eligible"]]
    lookup={(r["id_a"],r["id_b"]):r for r in rows}
    lookup.update({(b,a):r for (a,b),r in list(lookup.items())})
    cand=[]
    for a,b in EXAMPLES:
        z=lookup.get((a,b))
        if z is None:
            cand.append({"a":a,"b":b,"status":"NOT_PRESENT_IN_CURRENT_EXTRACTION"})
            continue
        # Rank within *all explored pairs* is descriptive, not a valid p-value
        # because these examples were selected after seeing the 2026 pilot.
        score=z["structural_score_exploratory"]
        rank=1+sum(v>score for v in pool)
        cand.append({**z,"source_selection":"POST_HOC_DISCOVERY","descriptive_rank":rank,
                     "eligible_comparison_pool_size":len(pool)})
    report={"schema":"voynich-exp003-skeleton-protrusion-pilot-v1",
      "scientific_verdict":"INCONCLUSIVE_NONCONFIRMATORY",
      "technical_measurements":"AUTOMATIC_DIFFERENTIAL_SHAPE_FEATURES",
      "source_provenance":sources,
      "source_ledger_digest_sha256":hashlib.sha256(LEDGER.read_bytes()).hexdigest(),
      "n_regions":len(regions),"n_cross_canvas_color_matched_pairs":len(rows),
      "n_complexity_eligible_pairs":len(pool),
      "descriptive_eligible_null_score_percentiles":{str(p):round(float(np.percentile(pool,p)),5) for p in (50,90,95,99)} if pool else {},
      "discovery_example_scores":cand,
      "best_exploratory_pairs":rows[:25],
      "validation_limits":[
        "Junction and endpoint counts of morphological skeletons are sensitive to pigment gaps and downsampling.",
        "Radial peaks and convexity defects are digital geometric proxies, not independently labelled historical branches.",
        "No independent blinded manual annotations, physical-size calibration or held-out validation.",
        "These source folios were already selected after inspection; null percentiles are descriptive, NOT statistical p-values.",
        "Section/scribe/codicology matching and BH-FDR unavailable in this six-canvas pilot: do not claim statistical PASS.",
        "Mirroring is tracked separately, anisotropic scaling and deformable registration disallowed.",
        "Scientific nulls are not met without independent folio-group held-out and medieval iconography controls."
      ]}
    path=Path(out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("REPORT",path,"REGIONS",len(regions),"PAIRS",len(rows),"ELIGIBLE",len(pool),flush=True)
    for c in cand:print("EXAMPLE",c.get("id_a"),c.get("id_b"),c.get("structural_score_exploratory"),c.get("structural_comparison_eligible"),flush=True)


def selftest():
    m=np.zeros((112,112),np.uint8)
    cv2.line(m,(54,92),(54,25),1,9)
    cv2.line(m,(54,44),(21,14),1,8)
    cv2.line(m,(54,44),(88,14),1,8)
    a=signature(m);b=signature(m.copy())
    assert a==b and a["endpoints"]>=2,a
    circ=np.zeros_like(m);cv2.circle(circ,(56,56),25,1,-1)
    c=signature(circ)
    assert c["notches"]==0,c
    assert not alignment_score(c,c,{"shape_score":1.0})["structural_comparison_eligible"]
    score=alignment_score(a,b,{"shape_score":1.0})
    assert score["structural_score_exploratory"]==1.0,score
    print("SELFTEST_PASS deterministic branching, circle-negative, identical-shape 1.0",a,flush=True)


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",default=str(HERE/"branch_geometry_pilot_2026-10-09.json"))
    ap.add_argument("--selftest",action="store_true")
    args=ap.parse_args()
    selftest() if args.selftest else run(args.output)
