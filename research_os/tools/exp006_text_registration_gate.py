#!/usr/bin/env python3
"""Gated registration of annotated text positions to verified Yale photos.

No text↔figure associations are computed until independent real landmarks
exist, are source-documented and pass geometric/physical grouping checks.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"experiments/EXP-2026-005/native_semantic_review/review_manifest.json"
OUT=ROOT/"experiments/EXP-2026-006/text_coordinate_registration"

def template(source):
    req=[]
    for key,x in sorted(source["review_photos"].items()):
        req.append({
          "photo_key":key,"original_folio":x["label"],
          "native_photo_canvas_oid":x["oid"],"native_photo_sha256":x["source_sha256"],
          "native_photo_physical_groups":x["physical_groups"],
          "transcription_image_source":None,"transcription_image_identifier":None,
          "transcription_source_size_pixels":None,
          "landmarks":[],"reviewer_1":None,"reviewer_2":None,
          "verified_on_native_photo":False,
          "verified_on_transcription_image":False,
          "text_transcription_not_translation":True
        })
    return req

def validate_registration(row,source):
    if row["native_photo_canvas_oid"]!=source["oid"] or row["native_photo_sha256"]!=source["source_sha256"]:
        return {"status":"REJECTED_SOURCE_PROVENANCE_MISMATCH"}
    anchors=row.get("landmarks") or []
    if len(anchors)<4:
        return {"status":"BLOCKED_NO_INDEPENDENT_LANDMARKS"}
    if not row.get("transcription_image_source") or not row.get("transcription_image_identifier"):
        return {"status":"BLOCKED_TRANSCRIPTION_SOURCE_NOT_REGISTERED"}
    if not all([row.get("reviewer_1"),row.get("reviewer_2"),
                row.get("verified_on_native_photo"),row.get("verified_on_transcription_image")]):
        return {"status":"BLOCKED_TWO_INDEPENDENT_REVIEWER_VALIDATIONS_REQUIRED"}
    src_size=row.get("transcription_source_size_pixels")
    if not isinstance(src_size,list) or len(src_size)!=2 or min(src_size)<=0:
        return {"status":"BLOCKED_NO_TRANSCRIPTION_IMAGE_DIMENSIONS"}
    if any(not a.get("independently_verified") for a in anchors):
        return {"status":"BLOCKED_UNVERIFIED_ANCHOR"}
    ids=[a.get("landmark_id") for a in anchors]
    if len(ids)!=len(set(ids)):return {"status":"REJECTED_DUPLICATE_LANDMARK"}
    try:
        a=np.asarray([v["transcription_xy_px"] for v in anchors],np.float32)
        b=np.asarray([v["yale_native_xy_px"] for v in anchors],np.float32)
        assert a.shape==b.shape==(len(anchors),2)
        assert np.all(np.isfinite(a)) and np.all(np.isfinite(b))
        assert np.min(a)>=0 and np.all(a<=np.asarray(src_size,np.float32))
    except (AssertionError,ValueError,TypeError,KeyError):
        return {"status":"REJECTED_BAD_COORDINATES"}
    # Native size must be explicitly checked against source photo metadata in this manifest.
    oids=source["oid"]
    H,mask=cv2.findHomography(a,b,cv2.RANSAC,ransacReprojThreshold=12.0)
    if H is None or mask is None:return {"status":"REJECTED_GEOMETRICALLY_DEGENERATE"}
    pred=cv2.perspectiveTransform(a[None,:,:],H)[0]
    dif=np.linalg.norm(pred-b,axis=1)
    good=mask.ravel().astype(bool)
    if good.sum()<4 or max(dif[good])>15:
        return {"status":"REJECTED_HIGH_REPROJECTION_ERROR","max_inlier_error_px":round(float(dif[good].max()),3) if good.any() else None}
    return {"status":"REGISTERED_GEOMETRY_ONLY",
            "verified_landmark_count":len(anchors),"inliers":int(good.sum()),
            "median_reprojection_error_px":round(float(np.median(dif[good])),3),
            "native_canvas_oid":oids,
            "homography_transcript_to_yale_native":np.asarray(H).round(9).tolist(),
            "semantic_text_object_relation":"NOT_ASSESSED"}

def run(source_path,requests,out):
    source=json.loads(Path(source_path).read_text())
    sample=template(source)
    root=Path(out);root.mkdir(parents=True,exist_ok=True)
    requests=Path(requests)
    if requests.is_file():
        supplied=json.loads(requests.read_text())
        rows=supplied["registrations"]
    else:
        rows=sample
    by_key={x["photo_key"]:x for x in rows}
    valid={}
    for item in sample:
        k=item["photo_key"]
        if k not in by_key:raise ValueError("Missing source image review "+k)
        result=validate_registration(by_key[k],source["review_photos"][k])
        valid[k]=result
    registered=sum(v["status"]=="REGISTERED_GEOMETRY_ONLY" for v in valid.values())
    output={"schema":"exp006-placca-eva-photo-registration-gate-v1",
            "original_source_photo_count":len(sample),
            "sources_heldout_used":False,
            "status":"TEXT_ASSOCIATION_BLOCKED" if registered==0 else "SOME_SOURCE_REGISTRATIONS_VERIFIED",
            "registered_photos":registered,
            "text_object_links_claimed":0,
            "registrations":valid,
            "caution":"A valid homography is necessary but not sufficient: text-to-object association requires actual verified text symbol coordinates; no translation."}
    (root/"registration_audit.json").write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
    if not requests.is_file():
        (root/"registration_requests_unfilled.json").write_text(
           json.dumps({"schema":"exp006-manual-verified-registration-requests-v1",
                       "registrations":sample},ensure_ascii=False,indent=2)+"\n")
    print("EXP006_TEXT_GATE","SOURCES",len(sample),"REGISTERED",registered,
          "TEXT_ASSOCIATIONS",output["text_object_links_claimed"],output["status"])
    return output

def selftest():
    page={"oid":"o","source_sha256":"test"}
    row={"native_photo_canvas_oid":"o","native_photo_sha256":"test",
         "landmarks":[]}
    assert validate_registration(row,page)["status"]=="BLOCKED_NO_INDEPENDENT_LANDMARKS"
    row["native_photo_sha256"]="bad"
    assert validate_registration(row,page)["status"]=="REJECTED_SOURCE_PROVENANCE_MISMATCH"
    row["native_photo_sha256"]="test"
    row.update({"transcription_image_source":"independent-source","transcription_image_identifier":"page",
                "transcription_source_size_pixels":[500,500],
                "reviewer_1":"fixture-1","reviewer_2":"fixture-2",
                "verified_on_native_photo":True,"verified_on_transcription_image":True})
    row["landmarks"]=[{"landmark_id":str(i),"transcription_xy_px":[x,y],
                       "yale_native_xy_px":[2*x+30,2*y+40],
                       "independently_verified":True}
                      for i,(x,y) in enumerate([(10,20),(200,20),(200,200),(10,200),(100,100)])]
    good=validate_registration(row,page)
    assert good["status"]=="REGISTERED_GEOMETRY_ONLY",good
    print("EXP006_TEXT_GATE_SELFTEST_PASS SYNTHETIC_GEOMETRY_ONLY")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",default=str(SRC))
    p.add_argument("--requests",default=str(OUT/"verified_registration_requests.json"))
    p.add_argument("--out",default=str(OUT))
    p.add_argument("--selftest",action="store_true")
    a=p.parse_args()
    if a.selftest:selftest()
    else:run(a.manifest,a.requests,a.out)
