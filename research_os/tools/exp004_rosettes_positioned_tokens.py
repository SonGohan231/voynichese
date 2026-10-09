#!/usr/bin/env python3
"""EXP004: external position/orientation metadata for Rosettes f85v/f86r.

Data credit Alessandro Placa, Voynich Spatial Data, CC BY 4.0, and editorial
underlying EVA/ZL3b credits noted by author. The read/position of any token
is not a decipherment. The overlay coordinate frame is not the Yale JPEG.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"experiments"/"EXP-2026-004"/"rosettes_positioned_token_audit_v1.json"
REF="7580dafa624cf23a63665f4819022003f8d128ef"
OWNER="alessandroplaca-uro/voynich-spatial-data"
FILE="rosettes/tokens_f85v_86r.csv"
SOURCE=f"https://raw.githubusercontent.com/{OWNER}/{REF}/{FILE}"
EXPECTED_GIT_BLOB_SHA1="a5311d1b40d53731fc0453d5ecfbee456c4e2b9a"

def git_blob_sha1(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()

def circular_distance(a,b):
    return abs(((a-b+90)%180)-90)

def audit(csv_text,source_info=None):
    records=list(csv.DictReader(io.StringIO(csv_text)))
    if len(records)!=539:raise ValueError(f"Unexpected token count {len(records)} != 539")
    seen=set();validated=[];by_region=defaultdict(list)
    for row in records:
        tid=row["id"];paragraph=row["paragraph"]
        if tid in seen:raise ValueError("Duplicate transcription token id")
        seen.add(tid)
        x,y,angle=(float(row["x_px"]),float(row["y_px"]),float(row["angle_deg"]))
        if not(0<=x<=2412 and 0<=y<=2375 and math.isfinite(angle)):
            raise ValueError(f"Out of Placa overlay bounds: {tid}")
        token=row["token"].strip()
        if not token:continue
        data={"id":tid,"region_id":paragraph,"transliteration":token,
              "x_overlay_fraction":round(x/2412,6),"y_overlay_fraction":round(y/2375,6),
              "angle_deg_cw_screen":round(angle%360,2),
              "source_label":row.get("source"),"gallow_family":row.get("gallow_family"),
              "transcription_certainty":"EXTERNAL_DATASET_NOT_INDEPENDENTLY_ADJUDICATED"}
        validated.append(data);by_region[paragraph].append(data)
    freq=Counter(t["transliteration"] for t in validated)
    directions=Counter(int(t["angle_deg_cw_screen"]//30)%12 for t in validated)
    group_summaries=[]
    for paragraph,items in sorted(by_region.items(),key=lambda k:int(k[0])):
        cx=sum(t["x_overlay_fraction"] for t in items)/len(items)
        cy=sum(t["y_overlay_fraction"] for t in items)/len(items)
        a=[math.radians(t["angle_deg_cw_screen"]) for t in items]
        meanangle=math.degrees(math.atan2(sum(math.sin(z) for z in a),sum(math.cos(z) for z in a)))%360
        group_summaries.append({
            "region_id":paragraph,"positioned_tokens":len(items),
            "center_overlay_normalized_xy":[round(cx,5),round(cy,5)],
            "mean_token_rotation_deg":round(meanangle,2),
            "distinct_transcribed_forms":len({t["transliteration"] for t in items})
        })
    seen_by_region=defaultdict(list)
    for t in validated:seen_by_region[t["transliteration"]].append(t)
    forms_in_multiple_regions=[]
    for token,occ in seen_by_region.items():
        paragraphs={z["region_id"] for z in occ}
        if len(paragraphs)<2:continue
        angles=[z["angle_deg_cw_screen"] for z in occ]
        max_orient_gap=max((circular_distance(a,b) for a in angles for b in angles),default=0)
        forms_in_multiple_regions.append({
           "form":token,"occurrences":len(occ),"region_count":len(paragraphs),
           "maximum_angular_distance_mod_180":round(max_orient_gap,2),
           "unique_region_ids":sorted(paragraphs,key=int),
        })
    forms_in_multiple_regions.sort(key=lambda r:(-r["region_count"],-r["occurrences"],r["form"]))
    return {
       "schema":"exp004-f85v-f86r-positioned-token-layout-v1",
       "provenance":source_info or {},
       "license":"CC BY 4.0, attribution to Alessandro Placa, underlying EVA/ZL3b transcription credits apply",
       "scientific_status":"EXPLORATORY_LAYOUT_ONLY",
       "coordinate_reference":"Placa overlay image frame 2412x2375, NOT aligned to source Yale canvas 1006231 7925x7268",
       "total_positioned_transcription_tokens":len(validated),
       "transcription_regions_count":len(by_region),
       "unique_token_forms":len(freq),
       "direction_bins_30deg_clockwise":dict(sorted(directions.items())),
       "top_forms":[{"form":k,"count":v} for k,v in freq.most_common(30)],
       "region_summaries":group_summaries,
       "form_recurrence_across_regions":forms_in_multiple_regions[:150],
       "token_locations":validated,
       "not_yet_tested":[
          "Original Yale image to Placa frame homography or control point correspondence",
          "Rosette centers and independently verified sector/label association",
          "Other folios token-label co-location analysis with section/scribe Currier controls",
          "Meaning of tokens or physical direction of read flow",
          "Robustness to alternative transliteration versions or editorial reading order",
       ]
    }

def main(out):
    req=urllib.request.Request(SOURCE,headers={"User-Agent":"VoynichEXP004Transcription/1.0"})
    with urllib.request.urlopen(req,timeout=60) as src:
        blob=src.read(2_000_000)
    observed=git_blob_sha1(blob)
    if observed!=EXPECTED_GIT_BLOB_SHA1:
        raise RuntimeError(f"External pinned source bytes Git blob mismatch! {observed}")
    metadata={"source_url":SOURCE,"source_commit":REF,
      "source_git_blob_sha1":observed,"csv_sha256":hashlib.sha256(blob).hexdigest()}
    doc=audit(blob.decode("utf-8-sig"),metadata)
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(doc,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("EXP004_TRANSCRIPTION",doc["total_positioned_transcription_tokens"],
          "REGIONS",doc["transcription_regions_count"],
          "FORMS",doc["unique_token_forms"],"REPEATED_REGION_FORMS",
          len(doc["form_recurrence_across_regions"]),"OUTPUT",out,flush=True)

def selftest():
    assert circular_distance(179,1)==2
    assert circular_distance(5,175)==10
    assert git_blob_sha1(b"hello")==hashlib.sha1(b"blob 5\x00hello").hexdigest()
    print("EXP004_TOKEN_SELFTEST_PASS angle equivalence and content-addressed source hash")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",default=str(OUT))
    p.add_argument("--selftest",action="store_true")
    a=p.parse_args()
    if a.selftest:selftest()
    else:main(a.output)
