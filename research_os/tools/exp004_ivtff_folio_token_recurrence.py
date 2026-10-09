#!/usr/bin/env python3
"""EXP004: source-provenance, form recurrence by folio/locus type, ZL3b IVTFF.

Based on Rene Zandbergen's published ZL3b 2025 transliteration.
Statistical forms are NOT historical word meanings; uncertain markup excluded.
Original text is not redistributed, only derived counts and source hashes.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import hashlib
import json
import re
from pathlib import Path
import urllib.request
from itertools import combinations

HERE=Path(__file__).resolve().parents[1]/"experiments"/"EXP-2026-004"
SOURCE_URL="https://www.voynich.nu/data/ZL3b-n.txt"
PAGE_RE=re.compile(r"^<(f\d+[rv]\d*|fRos)>\s*(?:<!\s*(.*?)\s*>)?")
LOCUS_RE=re.compile(r"^<(?P<folio>f[^.>]+)\.(?P<line>\d+[a-z]?),(?P<mark>[@+\-=*&~/])(?P<locus>[PLCR])(?P<rest>[^>]*)>\s*(?P<value>.*)$")
VARS_RE=re.compile(r"\$([A-Z])=([A-Za-z0-9]+)")
COMMENT_RE=re.compile(r"<!.*?>")
OTHER_TAG_RE=re.compile(r"<[^>]*>")
UNCERTAIN_TOKENS=re.compile(r"[\[\]{}/?@:\'0-9]")
SPLIT_RE=re.compile(r"[.,\s]+")

def tokenize_strict(value):
    # Exclude editorial uncertain readings instead of treating alternatives as
    # separate observed words; avoid orthographic reverse conversion.
    stripped=COMMENT_RE.sub(" ",value)
    stripped=OTHER_TAG_RE.sub(".",stripped)
    raw=SPLIT_RE.split(stripped)
    return [t for t in raw if re.fullmatch(r"[a-z]+",t) and not UNCERTAIN_TOKENS.search(t)]

def parse_file(text):
    folios={};lines=[];current=None;unparsed=[]
    for row in text.splitlines():
        row=row.strip()
        if not row or row.startswith("#"):continue
        page=PAGE_RE.match(row)
        if page:
            current=page.group(1)
            props={k:v for k,v in VARS_RE.findall(page.group(2) or "")}
            folios[current]={"meta":props,"loci":Counter(),"tokens":Counter(),"labels":Counter(),
                             "token_loci":defaultdict(set)}
            continue
        match=LOCUS_RE.match(row)
        if match:
            f=match.group("folio")
            if f not in folios:
                raise ValueError(f"Unrecognized folio location {f}")
            locus=match.group("locus")
            toks=tokenize_strict(match.group("value"))
            folios[f]["loci"][locus]+=1
            folios[f]["tokens"].update(toks)
            if locus in ("L","C","R"):folios[f]["labels"].update(toks)
            for tok in set(toks):folios[f]["token_loci"][tok].add(locus)
            lines.append({"folio":f,"locus_type":locus,"accepted_token_count":len(toks),
                          "line_number":match.group("line")})
        elif row.startswith("<f"):
            unparsed.append(row[:160])
    return folios,lines,unparsed

def source_key_to_canvas(label):
    # 206 original photos group some facing folds and cut pages in one canvas.
    text=label.lower()
    return re.findall(r"(?<!\d)(\d{1,3}[rv]\d?)(?!\d)",text)

def build(content):
    folios,lines,unparsed=parse_file(content)
    if len(folios)<100 or len(lines)<5385 or unparsed:
        raise ValueError("Source file failed corpus coverage checks")
    label_occurrences=defaultdict(list)
    for folio,d in folios.items():
        for token,count in d["labels"].items():
            label_occurrences[token].append({"folio":folio,"count":count,
                                               "Currier":d["meta"].get("L"),
                                               "scribe":d["meta"].get("H")})
    observed=[(token,rows) for token,rows in label_occurrences.items()
              if 2<=len(rows)<=12 and len(token)>=3]
    pairs=Counter()
    shared_forms=defaultdict(list)
    for token,rows in observed:
        for a,b in combinations(rows,2):
            x,y=sorted((a["folio"],b["folio"]))
            pairs[(x,y)]+=1
            shared_forms[(x,y)].append(token)
    ranked=[]
    for (a,b),n in pairs.most_common(120):
        ma=folios[a]["meta"];mb=folios[b]["meta"]
        ranked.append({"folio_a":a,"folio_b":b,"shared_rare_label_forms":n,
           "example_forms":sorted(shared_forms[(a,b)])[:20],
           "currier_a":ma.get("L"),"currier_b":mb.get("L"),
           "scribe_a":ma.get("H"),"scribe_b":mb.get("H"),
           "same_object":"NOT_ESTABLISHED","source_crop_alignment":"NOT_AVAILABLE",
           "scientific_status":"DISCOVERY_PAIR_NOT_INDEPENDENT"})
    return {
        "schema":"exp004-zl3b-folio-token-locus-recurrence-v1",
        "source":SOURCE_URL,
        "translation_or_decipherment":"NOT_PERFORMED",
        "status":"EXPLORATORY_NOT_CONFIRMATORY",
        "page_header_count":len(folios),"locus_lines_parsed":len(lines),
        "unparsed_source_locus_like_line_count":len(unparsed),
        "unparsed_source_examples":unparsed[:18],
        "counts_by_locus_type":dict(Counter(row["locus_type"] for row in lines)),
        "folios_with_label_tokens":sum(bool(d["labels"]) for d in folios.values()),
        "strict_filtered_token_count":sum(sum(d["tokens"].values()) for d in folios.values()),
        "folios":[{"folio":f,"locus_count":sum(d["loci"].values()),
                    "loci_by_type":dict(d["loci"]),
                    "strict_token_count":sum(d["tokens"].values()),
                    "strict_lcr_token_count":sum(d["labels"].values()),
                    "distinct_lcr_tokens":len(d["labels"]),
                    "currier_language":d["meta"].get("L"),"scribe":d["meta"].get("H"),
                    "section":d["meta"].get("I"),"page_variables":d["meta"]}
                   for f,d in sorted(folios.items())],
        "lcr_label_forms_across_folios":{
          "distinct_lcr_forms":len(label_occurrences),
          "candidate_rare_cross_folio_forms":len(observed),
          "cross_folio_recurrence_pairs":len(pairs)},
        "ranked_lcr_shared_forms_folio_pairs":ranked,
        "method_limits":[
          "Strict token filter drops all bracket alternatives, rare encoded characters, uncertain glyphs and compounds.",
          "L/C/R locus placement types are from IVTFF source annotations, not visually matched original bounding boxes.",
          "Common tokens might represent generic script patterns or section/scribe markers; no semantic meaning inferred.",
          "No manually aligned object ROI and text, no source image-to-locus coordinate mapping.",
          "No validated same object or alternate view, and this is exploratory pair mining without FDR/heldout.",
          "fRos source heading is not automatically equivalent to a specific Yale crop coordinate transform."
        ]}

def selftest():
    sample="""#=IVTFF Eva- 2.0 M 5
<f1r> <! $L=A $H=1 $I=T>
<f1r.1,@P0> <%>fachys.ykal.ar.ataiin.shol
<f1r.2,@Lp> ckhaiin.ol
<f1v> <! $L=A $H=1>
<f1v.1,@C0> ol.ykal
"""
    f,rows,unparsed=parse_file(sample)
    assert len(f)==2 and len(rows)==3 and not unparsed
    assert f["f1r"]["labels"]["ckhaiin"]==1
    assert f["f1v"]["labels"]["ol"]==1
    assert tokenize_strict("okar.[a:o]in.daiin") == ["okar","daiin"]
    print("EXP004_IVTFF_SELFTEST_PASS page variables L/C/R and strict ambiguity exclusions")

def main(path):
    req=urllib.request.Request(SOURCE_URL,headers={"User-Agent":"VoynichEXP004IVTFF/1.0"})
    with urllib.request.urlopen(req,timeout=75) as page:
        raw=page.read(5_000_000)
    if not raw.startswith(b"#=IVTFF"):raise ValueError("Source is not expected IVTFF header")
    txt=raw.decode("utf-8-sig")
    d=build(txt)
    d["input_sha256"]=hashlib.sha256(raw).hexdigest()
    d["external_source_version"]="ZL3b dated 2025-05-13; source web can be changed, digest frozen in output"
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("EXP004_IVTFF",d["page_header_count"],"PAGES",d["locus_lines_parsed"],"LOCI",
          "label-folios",d["folios_with_label_tokens"],
          "rare-form-folio-pairs",d["lcr_label_forms_across_folios"]["cross_folio_recurrence_pairs"],
          "LCR_SOURCE_SHA256",d["input_sha256"],flush=True)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",default=str(HERE/"zl3b_locus_token_folio_recurrence_v1.json"))
    ap.add_argument("--selftest",action="store_true")
    args=ap.parse_args()
    if args.selftest:selftest()
    else:main(args.output)
