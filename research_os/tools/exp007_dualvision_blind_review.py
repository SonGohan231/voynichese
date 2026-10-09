#!/usr/bin/env python3
"""EXP007: independently run two DIFFERENT pretrained vision models on 18 SHA-verified Voynich crops.

This is AI-only exploratory semantic screening, NOT independent human/historical annotation.
The two vision stages are separate processes; neither can read the other's predictions.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"experiments/EXP-2026-005/native_semantic_review"
OUT=ROOT/"experiments/EXP-2026-007/dual_vision"
FROZEN=OUT/"frozen_18_crop_manifest.json"
A=OUT/"pass_a_blip_captions.json"
B=OUT/"pass_b_clip_labels.json"
LABELS=[
 ("round_diagram","a medieval manuscript illustration showing a circular diagram with rings or radial lines"),
 ("architecture","a medieval manuscript illustration of a building, tower, wall or castle"),
 ("plant_part","a medieval botanical manuscript illustration of a leaf, root, branch or plant"),
 ("human_figure","a medieval manuscript illustration of a person or human figure"),
 ("celestial_symbols","a medieval diagram with stars, suns or moons"),
 ("handwriting","medieval handwritten text in lines, with no illustrated figure"),
 ("nonsemantic_markings","a manuscript photograph with only parchment, stray marks and ink noise")
]
PROMPTS=[x[1] for x in LABELS]
MODES=("freeze","caption","contrast","audit","selftest")

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def store(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")

def freeze(source=BASE,out=FROZEN):
    source=Path(source)
    manifest=json.loads((source/"review_manifest.json").read_text())
    by_photo={}
    for r in manifest["proposed_regions"]:
        by_photo.setdefault(r["crop_id"].split(":")[0],[]).append(r)
    photo_names=list(manifest["review_photos"])
    assert len(photo_names)==9
    data=[]
    # Deterministic source order. DO NOT view target-pair or performance ranking.
    for photo in photo_names:
        rows=sorted(by_photo[photo],key=lambda r:r["crop_id"])
        assert len(rows)==3
        for r in rows[:2]:
            img=source/r["crop_path"]
            if not img.is_file():raise FileNotFoundError(img)
            if sha(img)!=r["image_crop_sha256"]:raise ValueError("Wrong crop SHA for "+str(img))
            data.append({
                "id":r["crop_id"],"crop_file":r["crop_path"],
                "crop_sha256":r["image_crop_sha256"],
                "source_canvas_oid":str(r["source_oid"]),
                "source_photo_sha256":r["source_jpeg_sha256"],
                "physical_groups":r["physical_groups"],
                "source_native_bbox_xyxy":r["bbox_source_native_xyxy_px"],
                "source_native_label":r["label"],
                "proposal_kind":r["proposal_type"],
                "source_photo_verified_in_ancestor_workflow":True,
            })
    assert len(data)==18 and len(set(x["id"] for x in data))==18
    assert sum(x["proposal_kind"]=="NEUTRAL_COVERAGE_GRID_NOT_OBJECT" for x in data)>0
    package={
        "schema":"voynich-exp007-frozen-source-native-crops-v1",
        "freeze_policy":"first_two_ROIs_by_crop_id_per_Yale_photo_predeclared_without_prior_similarity_ranks",
        "science_level":"EXPLORATORY_NOT_SEMANTIC_GROUND_TRUTH",
        "source_pack_manifest_sha256":sha(source/"review_manifest.json"),
        "crop_count":len(data),"source_photo_count":len(photo_names),
        "excluded_data":"EXP-2026-001_HELDOUT",
        "partitions":{"A":"Salesforce/blip-image-captioning-base",
                      "B":"openai/clip-vit-base-patch32"},
        "crop_ids":data,
    }
    store(out,package)
    print("EXP007_FREEZE_PASS",len(data),"CROPS",len(photo_names),"PHOTO_GROUPS",flush=True)
    return package

def load_frozen(source=BASE,path=FROZEN):
    payload=json.loads(Path(path).read_text())
    assert payload["crop_count"]==18 and payload["source_photo_count"]==9
    assert sha(Path(source)/"review_manifest.json")==payload["source_pack_manifest_sha256"]
    for x in payload["crop_ids"]:
        if sha(Path(source)/x["crop_file"])!=x["crop_sha256"]:
            raise ValueError("Frozen source integrity failure "+x["id"])
    return payload

def run_caption(source=BASE,manifest=FROZEN,out=A):
    import torch
    from PIL import Image
    from transformers import BlipProcessor,BlipForConditionalGeneration
    if Path(B).exists():raise RuntimeError("Blind pass A must not see the pass B file")
    frozen=load_frozen(source,manifest)
    model_id="Salesforce/blip-image-captioning-base"
    torch.manual_seed(17)
    processor=BlipProcessor.from_pretrained(model_id)
    model=BlipForConditionalGeneration.from_pretrained(model_id).eval()
    records=[]
    for i,entry in enumerate(frozen["crop_ids"]):
        im=Image.open(Path(source)/entry["crop_file"]).convert("RGB")
        batch=processor(images=im,return_tensors="pt")
        with torch.inference_mode():
            token=model.generate(**batch,max_new_tokens=32,num_beams=2,do_sample=False)
        caption=processor.decode(token[0],skip_special_tokens=True)
        records.append({
            "id":entry["id"],"crop_sha256":entry["crop_sha256"],
            "caption_raw":caption,"category":"UNKNOWN",
            "semantic_trust":"UNVALIDATED_AI_CAPTION",
            "explicit_negative_or_unknown":"UNKNOWN",
            "source_oid":entry["source_canvas_oid"],
        })
        print("EXP007_BLIP",i+1,entry["id"],json.dumps(caption,ensure_ascii=False),flush=True)
    output={
       "schema":"exp007-blind-ai-pass-a-v1","model":model_id,
       "model_task":"free_visual_captioning_without_access_to_other_pass",
       "model_trust":"AI_ONLY_NO_HUMAN_VALIDATION",
       "model_checkpoint_revision":"DEFAULT_HF_REVISION_AT_EXECUTION_NOT_PINNED",
       "source_manifest_sha256":sha(manifest),"n":len(records),
       "records":records,"historical_semantics_accepted":0
    }
    store(out,output)
    print("EXP007_PASS_A_COMPLETED",len(records),flush=True)
    return output

def run_contrast(source=BASE,manifest=FROZEN,out=B):
    import torch
    from PIL import Image
    from transformers import CLIPModel,CLIPProcessor
    if Path(A).exists():raise RuntimeError("Blind pass B must not see the pass A file")
    frozen=load_frozen(source,manifest)
    torch.manual_seed(29)
    model_id="openai/clip-vit-base-patch32"
    processor=CLIPProcessor.from_pretrained(model_id)
    model=CLIPModel.from_pretrained(model_id).eval()
    records=[]
    for i,entry in enumerate(frozen["crop_ids"]):
        im=Image.open(Path(source)/entry["crop_file"]).convert("RGB")
        batch=processor(text=PROMPTS,images=im,padding=True,return_tensors="pt")
        with torch.inference_mode():
            logits=model(**batch).logits_per_image[0]
            probs=torch.softmax(logits.float(),dim=0).cpu().tolist()
        ranked=sorted(range(len(probs)),key=lambda n:-probs[n])
        top,second=ranked[:2]
        # Relative prompt scores are NOT calibrated class probabilities.
        # Mark UNKNOWN whenever substantially ambiguous.
        unreliable=probs[top]<.38 or (probs[top]-probs[second])<.15
        records.append({
           "id":entry["id"],"crop_sha256":entry["crop_sha256"],
           "scores_all_prompts":[{"label":LABELS[k][0],
                                 "prompt":PROMPTS[k],"relative_score":round(probs[k],6)}
                                 for k in range(len(probs))],
           "top_label":LABELS[top][0],
           "top_prompt_relative_score":round(probs[top],6),
           "second_relative_score":round(probs[second],6),
           "category": "UNKNOWN" if unreliable else LABELS[top][0],
           "unknown_reason": "LOW_PROMPT_SCORE_OR_MARGIN" if unreliable else None,
           "semantic_trust":"AI_ONLY_VOCABULARY_BIASED",
           "source_oid":entry["source_canvas_oid"],
        })
        print("EXP007_CLIP",i+1,entry["id"],LABELS[top][0],
              round(probs[top],3),"UNKNOWN" if unreliable else "CANDIDATE",flush=True)
    output={
       "schema":"exp007-blind-ai-pass-b-v1","model":model_id,
       "model_task":"zero_shot_relative_text_prompt_similarity_without_access_to_other_pass",
       "label_prompts":LABELS,
       "model_trust":"AI_ONLY_NO_HUMAN_VALIDATION",
       "model_checkpoint_revision":"DEFAULT_HF_REVISION_AT_EXECUTION_NOT_PINNED",
       "source_manifest_sha256":sha(manifest),"n":len(records),
       "records":records,"historical_semantics_accepted":0
    }
    store(out,output)
    print("EXP007_PASS_B_COMPLETED",len(records),flush=True)
    return output

def audit(manifest=FROZEN,pa=A,pb=B,out=OUT/"blind_vision_disagreements.json"):
    frozen=json.loads(Path(manifest).read_text())
    a=json.loads(Path(pa).read_text())
    b=json.loads(Path(pb).read_text())
    assert a["model"]!=b["model"] and a["source_manifest_sha256"]==b["source_manifest_sha256"]==sha(manifest)
    ra={x["id"]:x for x in a["records"]}
    rb={x["id"]:x for x in b["records"]}
    assert len(ra)==len(rb)==frozen["crop_count"]
    rows=[]
    for p in frozen["crop_ids"]:
        n=p["id"]
        la=ra[n];lb=rb[n]
        assert la["crop_sha256"]==lb["crop_sha256"]==p["crop_sha256"]
        rows.append({
          "id":n,"source_oid":p["source_canvas_oid"],
          "photo_sha":p["source_photo_sha256"],
          "source_native_bbox":p["source_native_bbox_xyxy"],
          "caption_a_raw":la["caption_raw"],
          "clip_b_top_class":lb["top_label"],
          "clip_b_status":lb["category"],
          "clip_b_prompt_scores":lb["scores_all_prompts"],
          "human_review":"NOT_PERFORMED",
          "automatic_semantic_agreement":"NOT_COMPARABLE_OPEN_VOCAB_CAPTION_VS_CLOSED_SET_PROMPTS",
          "adjudicated_historical_object_class":"UNKNOWN",
          "historical_same_object":False,
          "precise_object_polygon_semantic_mask":"NOT_AVAILABLE",
          "nearby_text_registered":"NOT_ASSESSED",
        })
    output={
      "schema":"voynich-exp007-two-distinct-ai-vision-runs-v1",
      "science_status":"AI_ONLY_HYPOTHESIS_GENERATION_NO_INDEPENDENT_HUMAN_VALIDATION",
      "source_manifest_sha256":sha(manifest),
      "model_a":a["model"],"model_b":b["model"],
      "image_count":len(rows),
      "no_cross_pass_visibility_during_inference":True,
      "two_separate_pretrained_vision_models":True,
      "two_independent_human_reviewers":False,
      "zero_historical_object_confirmations":True,
      "text_source_registered":False,
      "seal_exp001_heldout_untouched":True,
      "automatic_weak_classification_only":True,
      "crop_reviews":rows,
      "interpretation":"Use model outputs to schedule a truly independent original-scan object-level annotation; do not equate CLIP prompt softmax with calibrated truth or the BLIP prose with a historical fact.",
    }
    store(out,output)
    print("EXP007_AUDIT_PASS",len(rows),"REAL_MULTIMODAL_OBSERVATIONS",len(rows)*2,
          "HUMAN_SEMANTIC_VALIDATIONS",0,flush=True)
    return output

def selftest():
    src={
      "review_photos":{f"page{i}":{} for i in range(9)},
      "proposed_regions":[{"crop_id":f"page{i}:R{k}",
          "crop_file":"demo", "image_crop_sha256":"x"}
          for i in range(9) for k in range(1,4)]
    }
    assert len(src["review_photos"])==9 and len(src["proposed_regions"])==27
    assert len(LABELS)==7 and len(set(x[0] for x in LABELS))==len(LABELS)
    assert set(MODES)=={"freeze","caption","contrast","audit","selftest"}
    print("EXP007_DUALVISION_SELFTEST_PASS",flush=True)

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("stage",choices=MODES)
    cli.add_argument("--source",default=str(BASE))
    cli.add_argument("--manifest",default=str(FROZEN))
    cli.add_argument("--out",default=None)
    a=cli.parse_args()
    if a.stage=="selftest":selftest()
    elif a.stage=="freeze":freeze(a.source,a.out or a.manifest)
    elif a.stage=="caption":run_caption(a.source,a.manifest,a.out or A)
    elif a.stage=="contrast":run_contrast(a.source,a.manifest,a.out or B)
    elif a.stage=="audit":audit(a.manifest,out=a.out or OUT/"blind_vision_disagreements.json")
