#!/usr/bin/env python3
"""Ablate parchment/scan background and prior ROI selection from EXP005 ranks.

A forensic digital-image nuisance audit, not a Voynich semantic classifier.
"""
from __future__ import annotations
import argparse
import itertools
import json
import math
from pathlib import Path
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"experiments/EXP-2026-005/native_semantic_review"
STATS=ROOT/"experiments/EXP-2026-005/multi_family_feature_test"
SECTIONS=ROOT/"sources/beinecke_ms408_section_register.json"
MASKS=("GAUSSIAN_LOCAL","BACKGROUND_RESIDUAL")

def paper_proxy(path):
    im=cv2.imread(str(path),cv2.IMREAD_COLOR)
    if im is None:raise ValueError("Cannot read "+str(path))
    lab=cv2.cvtColor(im,cv2.COLOR_BGR2LAB)
    gray=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    bright=gray>=np.percentile(gray,75)
    if bright.sum()<20:raise ValueError("Insufficient unmasked bright pixels")
    # Brightest 25% pixel approximation, not parchment chemistry.
    return np.median(lab[bright],axis=0).astype(float)

def bg_score(a,b):
    dist=float(np.linalg.norm(a-b))
    return float(math.exp(-dist/40.))

def compute(manifest,feature,scored,section_ranges,out):
    pages=manifest["review_photos"]
    by_page={}
    by_id={}
    bg={}
    for r in manifest["proposed_regions"]:
        pg=r["crop_id"].split(":")[0]
        by_page.setdefault(pg,[]).append(r)
        by_id[r["crop_id"]]=r
        bg[r["crop_id"]]=paper_proxy(SOURCE/r["crop_path"])
    focus={frozenset([p["left"],p["right"]]):p["comparison"]
           for p in manifest["primary_comparisons"]}
    values=[]
    for a,b in itertools.combinations(sorted(by_page),2):
        left,right=pages[a],pages[b]
        if set(left["physical_groups"])&set(right["physical_groups"]):continue
        rel=("WITHIN" if sec(left["label"],section_ranges)==sec(right["label"],section_ranges)
             else "BETWEEN")
        combos=[]
        for pa,pb in itertools.product(by_page[a],by_page[b]):
            ia,ib=pa["crop_id"],pb["crop_id"]
            fg=[]
            for m in MASKS:
                va,vb=feature[ia][m],feature[ib][m]
                from exp005_multi_family_controls import count_sim,outline_sim,color_sim
                fg.append(.5*count_sim(va,vb)+.5*outline_sim(va,vb))
            combos.append({
                "a":ia,"b":ib,"source_kind_a":pa["proposal_type"],
                "source_kind_b":pb["proposal_type"],
                "no_color_score":min(fg),
                "paper_bright25_score":bg_score(bg[ia],bg[ib]),
            })
        fixed_a=next((x for x in by_page[a] if x["proposal_type"]=="NEUTRAL_COVERAGE_GRID_NOT_OBJECT"),None)
        fixed_b=next((x for x in by_page[b] if x["proposal_type"]=="NEUTRAL_COVERAGE_GRID_NOT_OBJECT"),None)
        neutral=next((x for x in combos if fixed_a and fixed_b and x["a"]==fixed_a["crop_id"] and x["b"]==fixed_b["crop_id"]),None)
        assert neutral and len(combos)==9
        v={
          "left":a,"right":b,"labels":[left["label"],right["label"]],
          "relation":rel,"focus":focus.get(frozenset([a,b])),
          "max_no_color":round(max(x["no_color_score"] for x in combos),6),
          "max_paper_bright25":round(max(x["paper_bright25_score"] for x in combos),6),
          "single_neutral_no_color":round(neutral["no_color_score"],6),
          "single_neutral_crop_ids":[neutral["a"],neutral["b"]],
          "winner_no_color":max(combos,key=lambda x:x["no_color_score"]),
        }
        values.append(v)
    control=[x for x in values if not x["focus"]]
    primary=[x for x in values if x["focus"]]
    assert len(control)==30 and len(primary)==5
    for p in primary:
        population=[x for x in control if x["relation"]==p["relation"]]
        p["controls_same_section_relation"]=len(population)
        for metric in ("max_no_color","max_paper_bright25","single_neutral_no_color"):
            p[metric+"_null_equal_or_better"]=sum(x[metric]>=p[metric] for x in population)
        p["scientific_status"]="MOTIF_REVIEW_ONLY_NO_IDENTITY"
    primary.sort(key=lambda x:-x["max_no_color"])
    report={
      "schema":"voynich-exp005-paper-roi-ablation-v1",
      "scientific_status":"INCONCLUSIVE_DIGITAL_PROXY_ONLY",
      "source_sha_provenance":"EXP005 SHA-reverified exact images and crop hashes in upstream job",
      "physical_pair_count":len(values),"primary_count":len(primary),"control_count":len(control),
      "ablations":{
        "max_no_color":"Best of nine cutouts, two mask passes, equal-weight count+outline, drop digital color",
        "max_paper_bright25":"Best of nine cutouts, LAB median of brightest 25 percent, proxy scan parchment only",
        "single_neutral_no_color":"First deterministic NEUTRAL grid crop per photograph: removes automatic hotspot selection but does NOT spatially register drawings",
      },
      "null_control":"Similar within-versus-between catalog section; same method, no p-value",
      "text_only":"NOT_ASSESSED",
      "EXP001_heldout_used":False,
      "no_semantic_object_identification":True,
      "mv3_mv4_confirmed":0,
      "primary":primary,
      "warnings":[
        "Brightest crop pixels are a crude background proxy, not verified bare parchment.",
        "Neutral grid windows cover different locations on different pages, so a weak result cannot disprove recurrence.",
        "Distinct scene classes and style confound nulls; all results selected post hoc, no valid p-values.",
        "Count/outline channels share monochrome segmentation and are not independent evidentiary families.",
      ]
    }
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("EXP005_ABLATION_PASS",len(values),"PAIRS",len(control),"NULLS")
    for x in primary:
        print("EXP005_ABLATION",x["focus"],
              "NO_COLOR",x["max_no_color"],x["max_no_color_null_equal_or_better"],"/",x["controls_same_section_relation"],
              "PAPER_BG",x["max_paper_bright25"],x["max_paper_bright25_null_equal_or_better"],"/",x["controls_same_section_relation"],
              "NEUTRAL",x["single_neutral_no_color"],x["single_neutral_no_color_null_equal_or_better"],"/",x["controls_same_section_relation"],
              "WINNER_TYPES",x["winner_no_color"]["source_kind_a"],x["winner_no_color"]["source_kind_b"])
    return report

def sec(label,sections):
    import re
    m=re.match(r"^(\d+)",label)
    if m is None:return "UNKNOWN"
    n=int(m.group(1))
    for x in sections["ranges"]:
        if x["first_folio"]<=n<=x["last_folio"]:return x["section_label"]
    return "UNKNOWN"

def selftest():
    a=np.array([200.,140.,130.])
    assert abs(bg_score(a,a)-1.0)<1e-9
    assert bg_score(a,a+20)<1
    assert sec("8v",{"ranges":[{"section_label":"BOTANICAL","first_folio":1,"last_folio":66}]})=="BOTANICAL"
    print("EXP005_ABLATION_SELFTEST_PASS")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",default=str(STATS/"paper_and_selection_ablation.json"))
    p.add_argument("--selftest",action="store_true")
    a=p.parse_args()
    if a.selftest:selftest()
    else:
        manifest=json.loads((SOURCE/"review_manifest.json").read_text())
        feature=json.loads((STATS/"crop_graph_proxy_features.json").read_text())
        scored=json.loads((STATS/"three_proxy_control_report.json").read_text())
        sections=json.loads(SECTIONS.read_text())
        assert scored["no_adjusted_p_values"] and not scored["source_heldout_used"]
        compute(manifest,feature,scored,sections,a.out)
