#!/usr/bin/env python3
"""EXP005 reproducible nonsemantic graph/appearance null-screen of native Yale ROI crops.

No human object labels and no decipherment. Two image segmentation algorithms are
not two independent human reviewers. Sealed EXP001 held-out is never opened.
"""
from __future__ import annotations
import argparse
import itertools
import json
import math
from pathlib import Path

import cv2
import numpy as np
from skimage.morphology import skeletonize

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/"experiments/EXP-2026-005/native_semantic_review"
SECTIONS = ROOT/"sources/beinecke_ms408_section_register.json"
OUT = ROOT/"experiments/EXP-2026-005/multi_family_feature_test"

def prep(bgr, size=360):
    h,w=bgr.shape[:2]
    scale=min((size-8)/w,(size-8)/h)
    im=cv2.resize(bgr,(max(1,round(w*scale)),max(1,round(h*scale))),interpolation=cv2.INTER_AREA)
    bg=np.full((size,size,3),np.median(bgr.reshape(-1,3),axis=0),dtype=np.uint8)
    x=(size-im.shape[1])//2;y=(size-im.shape[0])//2
    bg[y:y+im.shape[0],x:x+im.shape[1]]=im
    return bg,(x,y,im.shape[1],im.shape[0])

def clean_components(mask,lo=8):
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8),8)
    selected=np.zeros(mask.shape,np.uint8)
    regions=0
    for i in range(1,n):
        area=int(stats[i,cv2.CC_STAT_AREA])
        if lo<=area<=int(mask.size*.22):
            selected[lab==i]=1
            regions+=1
    return selected,regions

def mask_ink(gray,method):
    if method=="GAUSSIAN_LOCAL":
        raw=cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY_INV,37,10)
    elif method=="BACKGROUND_RESIDUAL":
        kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(23,23))
        background=cv2.morphologyEx(gray,cv2.MORPH_CLOSE,kernel)
        residual=cv2.subtract(background,gray)
        threshold,_=cv2.threshold(residual,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        raw=(residual>max(10,threshold)).astype(np.uint8)*255
    else:raise ValueError("Unregistered mask pass")
    return clean_components(raw>0)

def graph_measures(mask, components):
    sk=skeletonize(mask.astype(bool)).astype(np.uint8)
    neighbor=cv2.filter2D(sk.astype(np.uint8),cv2.CV_16S,
                         np.array([[1,1,1],[1,0,1],[1,1,1]],np.uint8),
                         borderType=cv2.BORDER_CONSTANT)
    ends=(sk>0)&(neighbor==1)
    nodes=((sk>0)&(neighbor>=3)).astype(np.uint8)
    junction=clean_components(nodes,1)[1]
    n, labels, stats, _=cv2.connectedComponentsWithStats((255*mask).astype(np.uint8),8)
    # A contour hole is a digital ring candidate, not a historical roundel.
    contours,hierarchy=cv2.findContours((255*mask).astype(np.uint8),cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
    holes=0
    if hierarchy is not None:
        holes=sum(1 for i,c in enumerate(contours)
                  if hierarchy[0][i][3]>=0 and cv2.contourArea(c)>=15)
    return {"stroke_components":int(components),"pixel_endpoints":int(ends.sum()),
            "junction_clusters":int(junction),"digital_holes":int(holes),
            "ink_pixel_fraction":round(float(mask.mean()),6),
            "skeleton_fraction":round(float(sk.mean()),6)}

def orientation(gray):
    # Gradient orientation describes raw strokes+page texture, not 2.5D pose.
    edge=cv2.Canny(gray,60,140)
    gx=cv2.Sobel(gray,cv2.CV_32F,1,0,ksize=3)
    gy=cv2.Sobel(gray,cv2.CV_32F,0,1,ksize=3)
    angle=np.mod(np.arctan2(gy,gx),math.pi)
    mag=cv2.magnitude(gx,gy)
    values=angle[edge>0]
    weight=mag[edge>0]
    hist=np.histogram(values,bins=12,range=(0,math.pi),weights=weight)[0]
    hist=hist/(hist.sum()+1e-8)
    return [round(float(x),6) for x in hist]

def appearance(bgr):
    hsv=cv2.cvtColor(bgr,cv2.COLOR_BGR2HSV)
    H,S,V=cv2.split(hsv)
    vivid=(S>=75)&(V>=70)
    red=vivid&((H<=12)|(H>=171))
    green=vivid&(H>=35)&(H<=90)
    blue=vivid&(H>=91)&(H<=133)
    return {"digital_red_fraction":round(float(red.mean()),6),
            "digital_green_fraction":round(float(green.mean()),6),
            "digital_blue_fraction":round(float(blue.mean()),6),
            "digital_high_saturation_fraction":round(float(vivid.mean()),6),
            "color_semantics":"UNKNOWN_SCAN_PAPER_PIGMENT"}

def descriptor(image,method):
    bgr,area=prep(image)
    x,y,w,h=area
    bgr=bgr[y:y+h,x:x+w] # ignore synthetic padding for source metrics
    gray=cv2.cvtColor(bgr,cv2.COLOR_BGR2GRAY)
    mask,components=mask_ink(gray,method)
    m=graph_measures(mask,components)
    m["direction_12bins"]=orientation(gray)
    m["appearance"]=appearance(bgr)
    m["mask_method"]=method
    m["photographic_ink_semantics"]="UNKNOWN_ALGORITHM_ONLY"
    return m,mask

def count_sim(a,b):
    keys=["stroke_components","pixel_endpoints","junction_clusters","digital_holes"]
    return float(np.mean([math.exp(-abs(math.log1p(a[k])-math.log1p(b[k])))
                          for k in keys]))

def outline_sim(a,b):
    p=np.asarray(a["direction_12bins"],float)
    q=np.asarray(b["direction_12bins"],float)
    h=max(0.,1-.5*np.abs(p-q).sum())
    fr=math.exp(-abs(math.log(1e-4+a["skeleton_fraction"])-
                     math.log(1e-4+b["skeleton_fraction"])))
    return float(.8*h+.2*fr)

def color_sim(a,b):
    names=["digital_red_fraction","digital_green_fraction",
           "digital_blue_fraction","digital_high_saturation_fraction"]
    va=np.array([a["appearance"][k] for k in names])
    vb=np.array([b["appearance"][k] for k in names])
    return float(math.exp(-10*np.abs(va-vb).mean()))

def score(a,b):
    n=count_sim(a,b);o=outline_sim(a,b);c=color_sim(a,b)
    # These channels are correlated. Combined score is only a review sorter.
    return {"count_only":round(n,5),"outline_only":round(o,5),
            "color_only":round(c,5),"composite_descriptive":round(.4*n+.4*o+.2*c,5)}

def section(label,sections):
    import re
    match=re.match(r"^(\d+)",label)
    if match is None:return "UNKNOWN"
    f=int(match.group(1))
    found=[x["section_label"] for x in sections["ranges"]
           if x["first_folio"]<=f<=x["last_folio"]]
    return found[0] if len(found)==1 else "UNKNOWN"

def compare_pair(aa,bb,desc,rows,methods):
    scores=[]
    for a in aa:
        for b in bb:
            rec={}
            for method in methods:
                rec[method]=score(desc[a["crop_id"]][method],
                                  desc[b["crop_id"]][method])
            scores.append((a["crop_id"],b["crop_id"],rec))
    # Both preprocessing algorithms must agree for a robust candidate;
    # MAX over 9 windows is treated identically for all control pairs.
    def stable_value(r):
        return min(r[m]["composite_descriptive"] for m in methods)
    scores.sort(key=lambda x:(-stable_value(x[2]),x[0],x[1]))
    a,b,sc=scores[0]
    return {"top_candidate_crops":[a,b],"score_passes":sc,
            "weak_pass_min_score":round(stable_value(sc),5),
            "all_9_window_pairs_tested":len(scores),
            "semantic_same_object":"NOT_ESTABLISHED",
            "full_null_correction":"NOT_RUN"}

def analyse(src_dir,section_json,out_dir):
    src_dir=Path(src_dir);out_dir=Path(out_dir);out_dir.mkdir(parents=True,exist_ok=True)
    j=json.loads((src_dir/"review_manifest.json").read_text(encoding="utf8"))
    s=json.loads(Path(section_json).read_text(encoding="utf8"))
    assert j["source_photos"]==9 and j["source_native_crops"]==27
    methods=("GAUSSIAN_LOCAL","BACKGROUND_RESIDUAL")
    desc={}
    photo={}
    for row in j["proposed_regions"]:
        path=src_dir/row["crop_path"]
        if not path.is_file():raise FileNotFoundError(str(path))
        import hashlib
        if hashlib.sha256(path.read_bytes()).hexdigest()!=row["image_crop_sha256"]:
            raise ValueError("Crop SHA256 mismatch")
        im=cv2.imread(str(path),cv2.IMREAD_COLOR)
        if im is None:raise ValueError("Unreadable image "+str(path))
        desc[row["crop_id"]]={}
        for method in methods:
            d,mask=descriptor(im,method)
            desc[row["crop_id"]][method]=d
        if row["source_jpeg_sha256"]!=j["review_photos"][row["crop_id"].split(":")[0]]["source_sha256"]:
            raise ValueError("Original JPEG archive mismatch")
        photo[row["crop_id"].split(":")[0]]=row
    groups={key:[] for key in j["review_photos"]}
    for row in j["proposed_regions"]:groups[row["crop_id"].split(":")[0]].append(row)
    pair_results=[]
    focus={tuple(sorted([x["left"],x["right"]])):x["comparison"] for x in j["primary_comparisons"]}
    for ak,bk in itertools.combinations(sorted(groups),2):
        a=j["review_photos"][ak];b=j["review_photos"][bk]
        if set(a["physical_groups"])&set(b["physical_groups"]):continue
        r=compare_pair(groups[ak],groups[bk],desc,j["proposed_regions"],methods)
        sa=section(a["label"],s);sb=section(b["label"],s)
        r.update({"left":ak,"right":bk,"folio_left":a["label"],"folio_right":b["label"],
                  "section_left":sa,"section_right":sb,
                  "section_relation":"UNKNOWN" if "UNKNOWN" in (sa,sb)
                  else ("WITHIN" if sa==sb else "BETWEEN"),
                  "preselected_name":focus.get((ak,bk)) or focus.get((bk,ak)),
                  "physical_group_independent":True})
        pair_results.append(r)
    primary=[p for p in pair_results if p["preselected_name"]]
    controls=[p for p in pair_results if not p["preselected_name"]]
    # DONT write inferential p-values: primary pairs were selected with prior
    # knowledge of shape similarity. The negative controls may also differ in
    # composition and section; these ranks are descriptive only.
    for p in primary:
        comparator=[x for x in controls if x["section_relation"]==p["section_relation"]]
        vals=[x["weak_pass_min_score"] for x in comparator]
        p["control_pairs_in_same_section_relation"]=len(vals)
        p["fraction_controls_with_equal_or_greater_weak_pass_score"]=(
           round(sum(x>=p["weak_pass_min_score"] for x in vals)/len(vals),5)
           if vals else None)
        p["descriptive_not_a_p_value"]=True
        p["scored_object_class"]="UNKNOWN"
        p["no_human_ground_truth"]=True
    primary.sort(key=lambda x:(-x["weak_pass_min_score"],x["preselected_name"]))
    result={
       "schema":"exp005-3proxy-negative-controls-v1",
       "science_status":"DESCRIPTIVE_NO_OBJECT_IDENTITY",
       "source_crop_manifest":str(src_dir/"review_manifest.json"),
       "independent_source_photos":len(j["review_photos"]),
       "image_crops_with_sha_verified":len(desc),
       "paired_physical_independent_photos":len(pair_results),
       "preselected_pairs":len(primary),
       "background_control_photo_pairs":len(controls),
       "two_algorithmic_passes":list(methods),
       "two_passes_are_not_independent_humans":True,
       "nulls":{"count_only":"COMPUTED_PIXEL_COMPONENT_PROXY",
                "outline_only":"COMPUTED_EDGE_ORIENTATION_PROXY",
                "color_only":"COMPUTED_DIGITAL_RGB_APPEARANCE_PROXY",
                "text_only":"NOT_ASSESSED_NO_GROUNDED_ROI_TO_TRANSCRIPT_ALIGNMENT"},
       "control_sampling":"ALL_DIFFERENT_PHYSICAL_GROUP_PHOTO_PAIRS; exclude preselected hypotheses; restrict control ranks by WITHIN/BETWEEN section",
       "no_adjusted_p_values":True,
       "source_heldout_used":False,
       "semantic_stars_women_towers_rings":"NOT_ANNOTATED",
       "mv2_or_above_accepted":0,
       "primary_results":primary,
       "controls":[{"folio_left":x["folio_left"],"folio_right":x["folio_right"],
                    "section_relation":x["section_relation"],
                    "weak_pass_min_score":x["weak_pass_min_score"]}
                   for x in controls],
       "caveats":[
           "Count-only and outline-only proxies arise from related image edges; not independent evidence.",
           "The 27 crops are selected with prior detectors and neutral windows; selection can bias ranks.",
           "Best of 9 ROI windows is chosen equally for targets and controls, still multiple testing.",
           "No source registered text ROIs: text-only cannot be reliably scored.",
           "Section type from Beinecke catalog is broad; no Currier/scribe stratification measured.",
           "Thinning/junctions and holes are digital segmentation proxies, NOT historic topology.",
           "No validated paint chemistry, semantic silhouettes, human face/pose labels or 2.5D model."
       ]
    }
    (out_dir/"three_proxy_control_report.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    (out_dir/"crop_graph_proxy_features.json").write_text(json.dumps(desc,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("EXP005_CONTROL_PASS","PHOTOS",len(j["review_photos"]),"CROPS",len(desc),
          "COMPARE",len(pair_results),"PRIMARY",len(primary),"CONTROLS",len(controls))
    for p in primary:
        print("EXP005_COMPARE",p["preselected_name"],"FOLIOS",p["folio_left"],p["folio_right"],
              "MIN_SCORE",p["weak_pass_min_score"],"NULL_COUNT",p["control_pairs_in_same_section_relation"],
              "CONTROL_GE",p["fraction_controls_with_equal_or_greater_weak_pass_score"],
              "VERDICT","INCONCLUSIVE")
    return result

def selftest():
    im=np.full((200,300,3),235,np.uint8)
    cv2.line(im,(65,25),(65,140),(25,25,25),5)
    cv2.line(im,(65,65),(130,110),(25,25,25),4)
    cv2.circle(im,(175,110),30,(20,20,20),3)
    a,mask=descriptor(im,"GAUSSIAN_LOCAL")
    b,mask2=descriptor(im,"BACKGROUND_RESIDUAL")
    assert a["stroke_components"]>=1
    assert 0<=count_sim(a,b)<=1.0001
    assert 0<=outline_sim(a,b)<=1.0001
    assert color_sim(a,b)<=1.0001
    assert len(a["direction_12bins"])==12
    assert len(mask.shape)==2
    ss={"ranges":[{"first_folio":1,"last_folio":66,"section_label":"BOTANICAL"}]}
    assert section("32r",ss)=="BOTANICAL" and section("67v",ss)=="UNKNOWN"
    print("EXP005_CONTROL_SELFTEST_PASS",flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",default=str(SOURCE))
    p.add_argument("--sections",default=str(SECTIONS))
    p.add_argument("--out",default=str(OUT))
    p.add_argument("--selftest",action="store_true")
    a=p.parse_args()
    if a.selftest:selftest()
    else:analyse(a.source,a.sections,a.out)
