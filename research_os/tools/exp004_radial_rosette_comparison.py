#!/usr/bin/env python3
"""EXP004 Rosettes: radial signature and ring/sector candidate comparison.

IMPORTANT: Hough circles are NOT a count of historical rosettes, and radial
peaks are NOT a verified star/spoke count. This candidate comparison can
suggest different folios needing blind source-native review, but cannot
establish a 2.5D identity or common object.
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
EXP2=ROOT/"experiments"/"EXP-2026-002"
EXP3=ROOT/"experiments"/"EXP-2026-003"
EXP4=ROOT/"experiments"/"EXP-2026-004"

def smooth(z,n=5):
    arr=np.asarray(z,dtype=np.float64)
    return sum(np.roll(arr,i) for i in range(-n//2+1,n//2+1))/n

def peaks_1d(profile,minimum_gap=3):
    x=np.array(profile,dtype=np.float64)
    if not len(x) or x.max()-x.min()<1e-9:return []
    sm=smooth(x,n=5)
    threshold=float(np.median(sm)+.7*np.std(sm))
    ids=np.flatnonzero((sm>np.roll(sm,1))&(sm>=np.roll(sm,-1))&(sm>threshold))
    kept=[]
    for k in sorted(ids,key=lambda i:-sm[i]):
        if all(min(abs(int(k)-int(z)),len(x)-abs(int(k)-int(z)))>=minimum_gap for z in kept):
            kept.append(int(k))
    return sorted(kept)

def signature_for_circle(image,center,radius):
    gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    edge=cv2.Canny(cv2.GaussianBlur(gray,(5,5),0),58,142,L2gradient=True)
    ntheta=72;nrad=75
    theta=np.arange(ntheta,dtype=float)*2*np.pi/ntheta
    normalized_r=np.linspace(.15,.93,nrad)
    # Estimate line frequency in annular/radial bins at previous Hough circle;
    # no physically calibrated coordinates, ring shade/ink may be overfit.
    coords=np.array([[(center[0]+radius*rr*np.cos(t),center[1]+radius*rr*np.sin(t))
                      for rr in normalized_r] for t in theta])
    xx=np.clip(np.round(coords[:,:,0]).astype(int),0,edge.shape[1]-1)
    yy=np.clip(np.round(coords[:,:,1]).astype(int),0,edge.shape[0]-1)
    sampled=(edge[yy,xx]>0).astype(np.float32)
    radial_sector=sampled[:,int(nrad*.18):int(nrad*.85)]
    angular=np.mean(radial_sector,axis=1)
    annular=np.mean(sampled,axis=0)
    # A uniform complete ring adds a roughly constant angular baseline, so
    # subtract it without claiming spokes or star rays.
    angular=np.maximum(0,angular-np.median(angular))
    annular=np.maximum(0,annular-np.median(annular))
    kangle=peaks_1d(angular,3)
    kring=peaks_1d(annular,4)
    return {"angular_profile":angular.round(4).tolist(),
            "radius_profile":annular.round(4).tolist(),
            "radial_line_peak_proposals":len(kangle),
            "annular_ring_peak_proposals":len(kring),
            "angular_peak_bin_ids":kangle,
            "ring_peak_bin_ids":kring,
            "edge_occupancy":round(float(sampled.mean()),5)}

def normalized_corr(x,y):
    a=np.asarray(x,dtype=float);b=np.asarray(y,dtype=float)
    if len(a)!=len(b):raise ValueError("profile lengths differ")
    a=a-np.mean(a);b=b-np.mean(b)
    denom=np.linalg.norm(a)*np.linalg.norm(b)
    return float(np.dot(a,b)/denom) if denom>1e-8 else 0.

def registration(a,b):
    # Test true cyclic ordering + reflection separately, neither implies a
    # physical front/back rotation unless independently established.
    z1=a["angular_profile"];z2=np.asarray(b["angular_profile"])
    scores=[]
    for reflected in (False,True):
        p=z2[::-1] if reflected else z2
        for shift in range(len(p)):
            scores.append((normalized_corr(z1,np.roll(p,shift)),shift,reflected))
    ang,shift,reflected=max(scores,key=lambda x:x[0])
    ring=normalized_corr(a["radius_profile"],b["radius_profile"])
    # Anti-pattern: circular silhouette similarity alone cannot validate
    # multiple identical partitions if peaks aren't present.
    enough=min(a["radial_line_peak_proposals"],b["radial_line_peak_proposals"])>=3
    enough= enough and min(a["annular_ring_peak_proposals"],b["annular_ring_peak_proposals"])>=2
    score=.67*max(0,ang)+.33*max(0,ring)
    if reflected:score-=.025
    return {"angular_correlation":round(ang,4),"ring_correlation":round(ring,4),
            "view_shift_in_5degree_bins":shift,"mirror":reflected,
            "score_exploratory":round(float(score),4),
            "rich_radial_evidence":bool(enough),
            "semantic_same_object":"NOT_ESTABLISHED",
            "different_view":"NOT_ESTABLISHED"}

def crop_url(oid,cx,cy,rad,w,h):
    xx=max(0.,(cx-rad)/w);yy=max(0.,(cy-rad)/h)
    right=min(1.,(cx+rad)/w);bottom=min(1.,(cy+rad)/h)
    q=[round(v*100,3) for v in (xx,yy,right-xx,bottom-yy)]
    return f"https://collections.library.yale.edu/iiif/2/{oid}/pct:{','.join(str(v) for v in q)}/!900,900/0/default.jpg"

def build(crosswalk,foldout,out):
    d=json.loads(Path(crosswalk).read_text(encoding="utf-8"))
    folds=json.loads(Path(foldout).read_text(encoding="utf-8"))
    entries={str(e["canvas_oid"]):e for e in d["archive_files"]}
    results=[]
    for record in folds["sources"]:
        oid=str(record["canvas_oid"])
        if oid not in entries:raise ValueError("Missing Yale provenance "+oid)
        e=entries[oid]
        orig=fetch_image(e)
        h,w=orig.shape[:2]
        scale=min(1,1800/max(w,h))
        im=cv2.resize(orig,(round(w*scale),round(h*scale)),
                      interpolation=cv2.INTER_AREA) if scale<1 else orig
        ww,hh=im.shape[1],im.shape[0]
        for j,p in enumerate(record.get("candidate_circular_regions",[])):
            x,y=p["center_xy"]
            c=(x*ww,y*hh)
            radius=p["radius_fraction_of_minimum_axis"]*min(ww,hh)
            if radius<10:continue
            sig=signature_for_circle(im,c,radius)
            results.append({
                "candidate_id":f"{oid}:circle:{j}",
                "canvas_oid":oid,"folio":e["yale_label"],
                "jpeg_sha256":e["imported_reported_sha256"],
                "source_original_wh":[w,h],
                "physical_groups":e["physical_group_ids"],
                "center_normalized":[x,y],
                "radius_frac_min_axis":p["radius_fraction_of_minimum_axis"],
                "hough_edge_support_fraction":p.get("edge_support_fraction"),
                "crop_uri":crop_url(oid,*c,radius,ww,hh),
                **sig,
                "historical_rosette_label":"UNVERIFIED_HOUGH_CANDIDATE",
                "true_sector_count":None,"true_star_count":None,
                "true_tower_count":None,"actual_spoke_count":None,
            })
        print("FOLDOUT_SOURCE",oid,e["yale_label"],"CIRCLES",len(record.get("candidate_circular_regions",[])),flush=True)
    matches=[]
    for a,b in itertools.combinations(results,2):
        if a["canvas_oid"]==b["canvas_oid"]:continue
        if set(a["physical_groups"]) & set(b["physical_groups"]):continue
        stats=registration(a,b)
        matches.append({"first":a["candidate_id"],"second":b["candidate_id"],
                        "folio_a":a["folio"],"folio_b":b["folio"],
                        "source_a":a["crop_uri"],"source_b":b["crop_uri"],
                        "angular_peak_proposals_a":a["radial_line_peak_proposals"],
                        "angular_peak_proposals_b":b["radial_line_peak_proposals"],
                        "ring_peak_proposals_a":a["annular_ring_peak_proposals"],
                        "ring_peak_proposals_b":b["annular_ring_peak_proposals"],
                        **stats})
    # High visual similarity is not sufficient; require richer internal
    # radial structure before presenting a pair as priority for manual review.
    matches.sort(key=lambda x:(not x["rich_radial_evidence"],-x["score_exploratory"],
                               x["folio_a"],x["folio_b"]))
    keep=[p for p in matches if p["rich_radial_evidence"]][:25]
    report={
       "schema":"exp004-foldout-radial-geometry-candidates-v1",
       "scientific_status":"EXPLORATORY_NOT_CONFIRMED",
       "scans_examined":len(set(x["canvas_oid"] for x in results)),
       "ring_hough_candidates_examined":len(results),
       "pair_count_between_separate_physical_groups":len(matches),
       "radial_rich_priority_candidates":len(keep),
       "geometry_method":"Canny edge sampled at 72 angular bins / 75 radii; local peaks only, not star/sector count",
       "provenance":{"archive_crosswalk_sha256":hashlib.sha256(Path(crosswalk).read_bytes()).hexdigest(),
                     "prior_foldout_probe_sha256":hashlib.sha256(Path(foldout).read_bytes()).hexdigest()},
       "regions":results,"crossfolio_candidates":keep,
       "calibration_warnings":[
         "Hough circles and angular/radius peaks are geometrical image PROPOSALS, not actual Rosettes/star/spoke counts.",
         "Input eight foldout photos selected exploratorily; original order and orientation not derived from geometry.",
         "Circular shift or mirror correlation is not 2.5D projection or evidence same object.",
         "Original archive SHA checked, but 1800px downsample used for angular signature.",
         "Angles and ring signal sensitive to ink gaps, scan shadows, fold creases and drawings overlapping a circle.",
         "All candidate similarity comparisons are exploratory selection; no clean heldout, adjusted p-values or semantic ground truth."
       ]
    }
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("EXP004_RADIAL_DONE",len(results),"CANDIDATE_PAIRS",len(matches),
          "PRIORITY",len(keep),"SCIENTIFIC",report["scientific_status"],flush=True)
    for x in keep[:10]:
        print("RADIAL_MATCH",x["folio_a"],x["folio_b"],x["score_exploratory"],
              x["angular_peak_proposals_a"],x["angular_peak_proposals_b"],flush=True)
    return report

def selftest():
    x=np.maximum(0,np.cos(np.arange(72)*2*np.pi/12))
    a={"angular_profile":x.tolist(),"radius_profile":np.maximum(0,np.cos(np.arange(75)*2*np.pi/8)).tolist(),
       "radial_line_peak_proposals":6,"annular_ring_peak_proposals":3}
    b=dict(a,angular_profile=np.roll(x,14).tolist())
    m=registration(a,b)
    assert m["angular_correlation"]>.99 and m["rich_radial_evidence"]
    c=dict(a,radial_line_peak_proposals=0)
    assert not registration(a,c)["rich_radial_evidence"]
    assert len(peaks_1d(np.zeros(72)))==0
    print("EXP004_RADIAL_SELFTEST_PASS shifted peaks, blank radial rejection, cyclic alignment")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--crosswalk",default=str(EXP2/"yale_archived_jpeg_provenance_crosswalk_2026-10-09.json"))
    p.add_argument("--foldout",default=str(EXP3/"foldout_geometry_probe_2026-10-09.json"))
    p.add_argument("--output",default=str(EXP4/"foldout_radial_matches_v1.json"))
    p.add_argument("--selftest",action="store_true")
    args=p.parse_args()
    if args.selftest:selftest()
    else:build(args.crosswalk,args.foldout,args.output)
