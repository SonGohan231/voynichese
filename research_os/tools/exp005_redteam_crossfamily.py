#!/usr/bin/env python3
"""Adversarial 3-proxy analysis: determine which EXP005 channel drives a high score.

All scores are exploratory. Features are algorithmic and correlated; not human
semantic objects, historical interpretation, inferential p-values or decipherment.
"""
from __future__ import annotations
import argparse
import itertools
import json
from pathlib import Path
import numpy as np
from exp005_multi_family_controls import score,section

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"experiments/EXP-2026-005/native_semantic_review"
STATS=ROOT/"experiments/EXP-2026-005/multi_family_feature_test"
SECTIONS=ROOT/"sources/beinecke_ms408_section_register.json"
METHODS=("GAUSSIAN_LOCAL","BACKGROUND_RESIDUAL")
CHANNELS=("count_only","outline_only","color_only","composite_descriptive")

def primary_and_null(manifest,features,sec):
    pages=manifest["review_photos"]
    rois={}
    for x in manifest["proposed_regions"]:
        key=x["crop_id"].split(":")[0]
        rois.setdefault(key,[]).append(x["crop_id"])
    assert len(rois)==9 and all(len(v)==3 for v in rois.values())
    focus={frozenset([x["left"],x["right"]]):x["comparison"]
           for x in manifest["primary_comparisons"]}
    data=[]
    for ak,bk in itertools.combinations(sorted(pages),2):
        a=pages[ak];b=pages[bk]
        if set(a["physical_groups"])&set(b["physical_groups"]):continue
        rel=("WITHIN" if section(a["label"],sec)==section(b["label"],sec)
             else "BETWEEN")
        candidates=[]
        for ia,ib in itertools.product(rois[ak],rois[bk]):
            parts={m:score(features[ia][m],features[ib][m]) for m in METHODS}
            vals={k:min(parts[m][k] for m in METHODS) for k in CHANNELS}
            candidates.append({"crop_a":ia,"crop_b":ib,"stable":vals,
                               "by_mask_method":parts})
        winner=max(candidates,key=lambda x:x["stable"]["composite_descriptive"])
        per_channel={k:max(x["stable"][k] for x in candidates) for k in CHANNELS}
        data.append({"a":ak,"b":bk,"labels":[a["label"],b["label"]],
                     "relation":rel,"focus":focus.get(frozenset([ak,bk])),
                     "per_channel_best_of_nine":per_channel,
                     "winner_same_pair":winner,
                     "comparable_physical_units":True})
    return data

def audit(data):
    control=[x for x in data if not x["focus"]]
    primary=[x for x in data if x["focus"]]
    for p in primary:
        group=[c for c in control if c["relation"]==p["relation"]]
        p["matched_null_count"]=len(group)
        p["channel_rank_audits"]={}
        for c in CHANNELS:
            value=p["per_channel_best_of_nine"][c]
            n=sum(x["per_channel_best_of_nine"][c]>=value for x in group)
            p["channel_rank_audits"][c]={
                "selected_best_of_nine_score":round(value,6),
                "same_relation_controls_equal_or_higher":n,
                "controls_n":len(group),
                "fraction_equal_or_higher_DESCRIPTIVE_NOT_PVALUE":
                   round(n/len(group),5) if group else None,
            }
        win=p["winner_same_pair"]["stable"]
        p["same_crop_pair_three_channels"]={c:round(win[c],6) for c in CHANNELS}
        p["warning"]="Algorithmic channel agreement is correlated, not three independent evidentiary families"
        p["judgment"]="MOTIF_REVIEW_ONLY_NO_SAME_OBJECT_IDENTITY"
    primary.sort(key=lambda x:-x["per_channel_best_of_nine"]["composite_descriptive"])
    return primary,control

def build(base,features_path,manifest_path,sections_path,out):
    base=json.loads(Path(base).read_text())
    feats=json.loads(Path(features_path).read_text())
    manifest=json.loads(Path(manifest_path).read_text())
    sec=json.loads(Path(sections_path).read_text())
    assert base["no_adjusted_p_values"] and base["mv2_or_above_accepted"]==0
    assert manifest["source_native_crops"]==27
    assert base["nulls"]["text_only"].startswith("NOT_ASSESSED")
    allpairs=primary_and_null(manifest,feats,sec)
    primary,control=audit(allpairs)
    assert len(primary)==5 and len(control)==30
    output={
      "schema":"exp005-adversarial-multi-channel-audit-v1",
      "scientific_status":"INCONCLUSIVE_NO_SEMANTIC_OBJECT_IDENTIFIED",
      "physical_independent_pair_count":len(allpairs),
      "background_null_pair_count":len(control),
      "target_pair_count":len(primary),
      "channel_names":list(CHANNELS),
      "mask_passes":list(METHODS),
      "crop_pairs_per_photo_pair":9,
      "null_by_within_between_sections":"DESCRIPTIVE_NOT_RANDOMIZED",
      "text_only_status":"NOT_ASSESSED_NEEDS_TRANSCRIPT_ROI_REGISTRATION",
      "source_photo_sha256":"REVERIFIED_IN_EXP005_UPSTREAM",
      "EXP001_heldout_used":False,
      "semantic_ground_truth":"NOT_ACQUIRED",
      "adjusted_significance":"NOT_ASSESSED",
      "MV3":0,"MV4":0,
      "preselected_pair_audits":primary,
      "controls_brief":[{"folios":x["labels"],"relation":x["relation"],
                         "per_channel_best_of_nine":x["per_channel_best_of_nine"]}
                         for x in control],
      "interpretation_boundaries":[
        "The high target pairs were preselected from exploratory prior analyses; null rank is not a p-value.",
        "Count and outline are derived from the same scan pixels and are not independent biological or historical object attributes.",
        "Text-only is deliberately unassessed until aligned label coordinate provenance is validated.",
        "All 9 crop combinations per photo pair are searched; null pairs receive identical opportunity.",
        "Within/between section labels are catalog classes, not scribe/Currier identifications.",
        "Any conclusion SAME_HISTORICAL_OBJECT needs two external blinded human image reviewers and original object masks.",
      ]
    }
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
    print("EXP005_REDTEAM_ANALYSED",len(primary),"TARGETS",len(control),"NULLS",flush=True)
    for p in primary:
        cols=" ".join(f"{k}={p['channel_rank_audits'][k]['same_relation_controls_equal_or_higher']}/{p['matched_null_count']}"
                      for k in CHANNELS)
        print("EXP005_REDTEAM",p["focus"],p["labels"],cols,"SAME_CROP",
              p["same_crop_pair_three_channels"],"VERDICT",p["judgment"],flush=True)
    return output

def selftest():
    mock={
      "review_photos":{"a":{"label":"8v","physical_groups":["QA"]},
                      "b":{"label":"32r","physical_groups":["QB"]}},
      "proposed_regions":[],
      "primary_comparisons":[{"left":"a","right":"b","comparison":"TEST"}]
    }
    for photo in ("a","b"):
        for i in range(3):
            mock["proposed_regions"].append({"crop_id":f"{photo}:R{i+1}"})
    a={"stroke_components":1,"pixel_endpoints":2,"junction_clusters":0,"digital_holes":0,
       "direction_12bins":[1/12]*12,"skeleton_fraction":.1,
       "appearance":{"digital_red_fraction":0.1,"digital_green_fraction":0,
                     "digital_blue_fraction":0,"digital_high_saturation_fraction":.1}}
    d={x["crop_id"]:{m:a for m in METHODS} for x in mock["proposed_regions"]}
    s={"ranges":[{"section_label":"BOTANICAL","first_folio":1,"last_folio":66}]}
    t=primary_and_null(mock,d,s)
    assert len(t)==1 and t[0]["focus"]=="TEST"
    assert t[0]["relation"]=="WITHIN"
    assert t[0]["per_channel_best_of_nine"]["count_only"]==1.
    print("EXP005_REDTEAM_SELFTEST_PASS",flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",default=str(STATS/"three_proxy_control_report.json"))
    p.add_argument("--features",default=str(STATS/"crop_graph_proxy_features.json"))
    p.add_argument("--manifest",default=str(SOURCE/"review_manifest.json"))
    p.add_argument("--sections",default=str(SECTIONS))
    p.add_argument("--out",default=str(STATS/"redteam_cross_channel_breakdown.json"))
    p.add_argument("--selftest",action="store_true")
    a=p.parse_args()
    if a.selftest:selftest()
    else:build(a.base,a.features,a.manifest,a.sections,a.out)
