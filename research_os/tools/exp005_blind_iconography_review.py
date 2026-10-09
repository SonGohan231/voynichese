#!/usr/bin/env python3
"""EXP005 two blinded source-native iconographic reviews: assignment & adjudication.

This does NOT manufacture semantic human labels, training sets, gold standard,
woman counts, star counts, tower counts, or same-object discoveries. It only
prepares 24 independent review assignments drawn from six Yale image source
packets, and rejects self-certification/zero-as-missing. Distinct human
annotators or separately validated specialist processes must sign A/B.
"""
import argparse
import hashlib
import json
import random
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXP4=ROOT/"experiments"/"EXP-2026-004"
SOURCE=EXP4/"native_review_packets"/"native_annotation_packet_index.json"
OUTPUT=EXP4/"two_blind_iconography_assignments"
TARGETS_PER_CANVAS=4
LABELS=["TOWER","MERLON","ROSETTE","RING","SECTOR","STAR","HUMAN_FIGURE",
        "FACE","LEFT_ARM","RIGHT_ARM","ROOT","STEM","LEAF","ORNAMENT","TEXT_LABEL",
        "FLOW_CHANNEL","UNKNOWN"]
FACES=["LEFT","RIGHT","FRONT","UP","DOWN","OBSCURED","UNKNOWN"]
PAINT=["APPEARS_PAINTED","APPEARS_UNCOLORED","OBSCURED","UNKNOWN"]
VERDICTS=["SAME_OBJECT_SUPPORTED","COMMON_MOTIF_ONLY","DIFFERENT_TOPOLOGY","UNKNOWN"]

def sha(s):
    return hashlib.sha256(str(s).encode("utf-8")).hexdigest()

def select_targets(index):
    sources={x["source_oid"] for x in index["source_pages"]}
    assert len(sources)==6,"Expected six verified original source canvases"
    chosen=[]
    for oid in sorted(sources):
        group=[r for r in index["review_targets"] if r["source_id"]==oid]
        if len(group)!=9:
            raise ValueError("All source photos must have exactly 9 true cropped tiles")
        order=sorted(group,key=lambda x:sha("EXP005_PARTITION_"+x["tile_id"]))
        chosen.extend(order[:TARGETS_PER_CANVAS])
    assert len(chosen)==24
    return chosen

def make_assignments(index):
    picked=select_targets(index)
    common={
        "schema":"voynich-exp005-independent-visual-review-v1",
        "declared_type":"REVIEWER_BLIND_PROPOSAL_TEMPLATE_NOT_GOLD",
        "source_manifest_digest_sha256":sha(json.dumps(index,sort_keys=True)),
        "source_canvas_count":6,
        "total_tasks":len(picked),
        "required_annotation_fields":{
           "entity_class":LABELS,"face_orientation":FACES,"paint_state":PAINT,
           "possible_identity":VERDICTS},
        "disallowed_inferences":["gender_from_bare_head_shape","meaning_of_Voynichese",
            "chemical_pigment_from_RGB","ZERO_COUNT_WHEN_UNINSPECTED",
            "same_3d_object_from_circle_contour_only"],
        "qualification_note":"Human-reviewed semantic gold >=24 true ROI and independent validation required."
    }
    output={}
    for reviewer in ("A","B"):
        assignments=[]
        for item in picked:
            assignments.append({
              "task_id":item["tile_id"],
              "source_oid":item["source_id"],
              "folio":item["folio_label"],
              "image_sha256":item["source_jpeg_sha256"],
              "native_source_bbox_xywh":item["native_pixel_bbox_xywh"],
              "review_tile_file":item["review_image"],
              "iiif_native_reference":item["iiif_native_crop_reference"],
              "is_image_inspected":False,
              "seen_other_reviewer_result":False,
              "annotator_id":None,
              "object_instances":None,
              "comments":None,
              "annotation_status":"UNREVIEWED"
            })
        random.Random(sha("EXP005_REVIEWER_"+reviewer)).shuffle(assignments)
        output[reviewer]={**common,"reviewer_slot":reviewer,"tasks":assignments}
    return output

def adjudicate(a,b):
    if a["reviewer_slot"]!="A" or b["reviewer_slot"]!="B":
        raise ValueError("Expected original A and B reviewer slots")
    aid={x["task_id"]:x for x in a["tasks"]}
    bid={x["task_id"]:x for x in b["tasks"]}
    if set(aid)!=set(bid) or len(aid)!=24:raise ValueError("Reviewer assignment mismatch")
    disagreements=[];complete=0;agreed=0
    for key in sorted(aid):
        x,y=aid[key],bid[key]
        if x["image_sha256"]!=y["image_sha256"] or x["native_source_bbox_xywh"]!=y["native_source_bbox_xywh"]:
            raise ValueError("Source provenance mismatch")
        inspected=(x["is_image_inspected"] and y["is_image_inspected"])
        if not inspected:continue
        if x["annotator_id"]==y["annotator_id"] or not x["annotator_id"] or not y["annotator_id"]:
            raise ValueError("Independent distinct annotator IDs required")
        if x["seen_other_reviewer_result"] or y["seen_other_reviewer_result"]:
            raise ValueError("Blindness broken")
        if x["object_instances"] is None or y["object_instances"] is None:
            raise ValueError("Inspected ROI requires list of objects; [] is allowed after full review")
        complete+=1
        ids=lambda items:sorted((item.get("entity_class"),item.get("face_orientation","UNKNOWN"),
                  item.get("paint_state","UNKNOWN")) for item in items)
        if ids(x["object_instances"])==ids(y["object_instances"]):agreed+=1
        else:disagreements.append(key)
    return {"schema":"voynich-exp005-adjudication-v1",
      "inspected_by_two_independent_annotators":complete,
      "fully_agreed_in_object_counts_and_coarse_class":agreed,
      "review_disagreements":disagreements,
      "uninspected_tasks":24-complete,
      "review_status":"PENDING_SOURCE_REVIEW" if complete<24 else
                      ("SECONDARY_ADJUDICATION_REQUIRED" if disagreements else "AGREED_NEEDS_GOLD_ADJUDICATION"),
      "accepted_same_object_cross_folio":0,
      "reason":"Tile agreement is necessary but never sufficient for semantic identity or 3D viewpoint."}

def prepare(source,out):
    index=json.loads(Path(source).read_text(encoding="utf-8"))
    assignments=make_assignments(index)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    for reviewer,record in assignments.items():
        (out/("reviewer_"+reviewer+"_BLINDED.json")).write_text(
          json.dumps(record,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    status=adjudicate(assignments["A"],assignments["B"])
    (out/"review_qualification_status.json").write_text(
      json.dumps(status,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("EXP005_TWO_BLIND_REVIEW",len(assignments["A"]["tasks"]),
          "TASKS",len(set(x["source_oid"] for x in assignments["A"]["tasks"])),
          "SOURCES",status["review_status"],"GOLD_COUNT",0,flush=True)

def selftest():
    fake={"source_pages":[{"source_oid":str(i)} for i in range(6)],
          "review_targets":[{"source_id":str(i),"tile_id":str(i)+":r"+str(j//3)+"c"+str(j%3),
            "folio_label":"f"+str(i)+"r","source_jpeg_sha256":sha(str(i)),
            "native_pixel_bbox_xywh":[0,0,100,100],"review_image":"example.jpg",
            "iiif_native_crop_reference":"https://collections.library.yale.edu/iiif/2/test"}
            for i in range(6) for j in range(9)]}
    a=make_assignments(fake)
    assert len(a["A"]["tasks"])==24
    assert {x["task_id"] for x in a["A"]["tasks"]}=={x["task_id"] for x in a["B"]["tasks"]}
    assert a["A"]["tasks"]!=a["B"]["tasks"]
    assert adjudicate(a["A"],a["B"])["review_status"]=="PENDING_SOURCE_REVIEW"
    assert adjudicate(a["A"],a["B"])["accepted_same_object_cross_folio"]==0
    print("EXP005_SELFTEST_PASS 24×2 blinded templates, unique per-ROI source hashes, missing-not-zero")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",default=str(SOURCE))
    p.add_argument("--out",default=str(OUTPUT))
    p.add_argument("--selftest",action="store_true")
    args=p.parse_args()
    selftest() if args.selftest else prepare(args.source,args.out)
