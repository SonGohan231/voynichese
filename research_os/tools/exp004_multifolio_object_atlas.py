#!/usr/bin/env python3
"""EXP004: source-linked multi-folio visual candidate atlas for Yale MS 408.

This is NOT a semantic object detector or a decipherment. Every putative
tower, person, star, rosette or alternative 2.5D perspective requires independent
human annotations + image-native evidence. No fake labels / absent-color claims.
Consumes the SHA-verified 206 image index of EXP003; never touches EXP001/002
sealed held-out observation data.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E2=ROOT/"experiments"/"EXP-2026-002"
E3=ROOT/"experiments"/"EXP-2026-003"
E4=ROOT/"experiments"/"EXP-2026-004"
INDEX=E3/"cv_full_2026-10-09.json"
CROSS=E2/"yale_archived_jpeg_provenance_crosswalk_2026-10-09.json"
FOLD=E3/"foldout_geometry_probe_2026-10-09.json"

CATEGORIES={
    "tower_turret_merlon":"NEEDS_HUMAN_SEMANTIC_ANNOTATION",
    "architecture_outline":"NEEDS_HUMAN_SEMANTIC_ANNOTATION",
    "ornament_border":"NEEDS_HUMAN_SEMANTIC_ANNOTATION",
    "connector_port":"NEEDS_HUMAN_SEMANTIC_ANNOTATION",
    "roundel_rosette":"CIRCULAR_GEOMETRY_PROPOSALS_ONLY",
    "ring_and_sector_divisions":"NEEDS_HUMAN_COUNT_AND_ALIGNMENT",
    "star_points_and_star_count":"NEEDS_HUMAN_COUNT_AND_ALIGNMENT",
    "human_figure_woman_count":"NEEDS_HUMAN_FIGURE_CLASSIFICATION",
    "face_direction":"NEEDS_HUMAN_ANGLE_ANNOTATION",
    "body_pose_and_orientation":"NEEDS_HUMAN_ANGLE_ANNOTATION",
    "plant_part":"NEEDS_HUMAN_SEMANTIC_ANNOTATION",
    "painted_color":"DIGITAL_APPEARANCE_ONLY",
    "unpainted_deliberately":"NOT_INFERABLE_FROM_RGB_NONDETECTION",
    "text_label":"REQUIRES_TRANSCRIPTION_AND_GEOMETRIC_ALIGNMENT",
    "voynichese_token":"REQUIRES_LICENSED_EVA_IVTFF_TEXT_WITH_CONFIDENCE",
}
# DHash is taken from automatically proposed crops in the prior CV pass;
# it is not invariant to mirrored views or arbitrary rotations.
def hamming64(a,b):
    if len(a)!=16 or len(b)!=16:
        raise ValueError("Expected 16-digit hexadecimal dHash64")
    return (int(a,16)^int(b,16)).bit_count()

def bbox_overlap_fraction(a,b):
    ax,ay,aw,ah=a; bx,by,bw,bh=b
    intersection=max(0.,min(ax+aw,bx+bw)-max(ax,bx))*max(0.,min(ay+ah,by+bh)-max(ay,by))
    return intersection/max(1e-12,aw*ah)

def text_safe_crop_url(oid,bbox):
    # Review link to original Yale IIIF, not proof of historic line identity.
    x,y,w,h=bbox
    x0=max(0.,x-.015);y0=max(0.,y-.015)
    rw=min(1-x0,w+.03);rh=min(1-y0,h+.03)
    return "https://collections.library.yale.edu/iiif/2/{}/pct:{},{},{},{}/!900,900/0/default.jpg".format(
       oid,*[round(float(v)*100,3) for v in (x0,y0,rw,rh)]
    )

def load_sources(index, cross):
    raw=json.loads(Path(index).read_text(encoding="utf-8"))
    ledger=json.loads(Path(cross).read_text(encoding="utf-8"))
    if raw.get("schema") != "exp-2026-003/yale-cv-pixel-appearance-v2":
        raise ValueError("Unexpected index schema, refuse mixing source versions")
    if raw.get("scope",{}).get("images_processed") !=206 or raw.get("failures"):
        raise ValueError("206 independently SHA-verified indexed JPEGs required")
    source={str(x["canvas_oid"]):x for x in ledger["archive_files"]}
    if len({str(e["canvas_oid"]) for e in ledger["archive_files"]})!=206:
        raise ValueError("Expected exactly 206 unique archive image identifiers")
    rows=raw["results"]
    if len(rows)!=206 or len(set(str(x["canvas_oid"]) for x in rows))!=206:
        raise ValueError("Missing or duplicated full inventory canvases")
    for row in rows:
        oid=str(row["canvas_oid"])
        if oid not in source or not row["jpeg_sha256_recomputed_match"]:
            raise ValueError("Missing independently preserved SHA source for canvas "+oid)
        e=source[oid]
        if row["source_path"]!=e["path"]:
            # the single duplicate 11r is represented from one of the archive batches.
            if oid!="1006096" or "11r" not in row["source_path"]:
                raise ValueError("Canvas path mismatch "+oid)
    return raw, source

def build_roi_records(index, source):
    rows=[]
    for page in index["results"]:
        oid=str(page["canvas_oid"])
        e=source[oid]
        for roi in page["rois"]:
            bbox=roi.get("bbox_normalized_xywh")
            if not bbox or len(bbox)!=4: continue
            bbox=[float(z) for z in bbox]
            if not all(0<=t<=1 for t in bbox) or bbox[2]<=0 or bbox[3]<=0:continue
            label=roi["label_type"]
            if label=="barwa_ciemne_linie":kind="dark_paint_or_ink_candidate"
            elif label.startswith("barwa_"):kind="color_appearance_component"
            else:kind="gray_outline_candidate"
            appearance=label[6:] if label.startswith("barwa_") else "NO_COLOR_SEMANTIC_CLASSIFICATION"
            item={
                "id":str(roi["id"]), "canvas_oid":oid,"folio_label":page["folio_label"],
                "source_jpeg_sha256":e["imported_reported_sha256"],
                "original_image_pixels":page["source_dimensions"],
                "physical_groups":page.get("physical_group_ids",[]),
                "source_bbox_xywh_norm":bbox,
                "source_yale_iiif_crop":text_safe_crop_url(oid,bbox),
                "source_yale_iiif_full":f"https://collections.library.yale.edu/iiif/2/{oid}/full/full/0/default.jpg",
                "area_fraction":float(roi.get("area_fraction",0)),
                "aspect_ratio":float(roi.get("aspect_ratio",0)),
                "hash64":str(roi.get("dhash64","")),
                "cv_proxy_class":kind,"color_appearance_class":appearance,
                "historical_object_class":"UNKNOWN", "human_annotated":False,
                "independently_verified":False,
                "perspective_direction":"UNKNOWN",
                "face_orientation":"UNKNOWN",
                "body_orientation":"UNKNOWN",
                "evidence":"AUTOMATIC_ROI_PROPOSAL_ONLY",
            }
            rows.append(item)
    return rows

def near_photograph_border(bbox):
    """Reject photographic framing and outer sheet borders from object identity."""
    x,y,w,h=[float(v) for v in bbox]
    return x<.12 or y<.08 or x+w>.88 or y+h>.92


def annotate_color_absence(rois):
    by_canvas=defaultdict(list)
    for r in rois:by_canvas[r["canvas_oid"]].append(r)
    # Bounding-box overlap is only a review suggestion, not a mask-based
    # "no pigment present" claim. Missing digital saturation ≠ missing paint.
    proxies=[]
    for page in by_canvas.values():
        colored=[r for r in page if r["cv_proxy_class"]=="color_appearance_component"]
        for r in page:
            if r["cv_proxy_class"]!="gray_outline_candidate":continue
            overlap=max((bbox_overlap_fraction(r["source_bbox_xywh_norm"],other["source_bbox_xywh_norm"])
                         for other in colored),default=0.)
            r["max_overlap_fraction_of_color_component_bbox"]=round(overlap,4)
            if overlap<.05 and not near_photograph_border(r["source_bbox_xywh_norm"]):
                r["colorless_outline_hypothesis"]="UNVERIFIED_CANDIDATE_LOW_COLOR_BBOX_OVERLAP"
                proxies.append(r["id"])
            else:r["colorless_outline_hypothesis"]="NO_CLAIM"
    return proxies

def eligible_pair(a,b):
    if a["canvas_oid"]==b["canvas_oid"]:return False
    # Do NOT present bifolio sides as independent samples.
    if set(a["physical_groups"]) & set(b["physical_groups"]):return False
    if a["cv_proxy_class"]!=b["cv_proxy_class"]:return False
    # Very dark contours and low-color ROI need not be in the same semantic class.
    if a["cv_proxy_class"]=="color_appearance_component" and a["color_appearance_class"]!=b["color_appearance_class"]:
        return False
    if not a["hash64"] or not b["hash64"]:return False
    ar_a=a["aspect_ratio"];ar_b=b["aspect_ratio"]
    if min(ar_a,ar_b)<=0:return False
    return abs(math.log(ar_a/ar_b))<.38

def find_pairs(rois,limit=125):
    buckets=defaultdict(list)
    for r in rois:
        # Mask class is a pixel label only, NEVER architecture/human/etc.
        key=(r["cv_proxy_class"],r["color_appearance_class"])
        buckets[key].append(r)
    candidates=[]
    for (kind,colour),items in buckets.items():
        for i,a in enumerate(items):
            for b in items[i+1:]:
                if not eligible_pair(a,b):continue
                h=hamming64(a["hash64"],b["hash64"])
                if h>9:continue
                ar_ratio=a["aspect_ratio"]/b["aspect_ratio"]
                if min(a["area_fraction"],b["area_fraction"])<=0:continue
                apparent_scale=math.sqrt(a["area_fraction"]/b["area_fraction"])
                candidates.append({
                    "roi_a":a["id"],"roi_b":b["id"],
                    "canvas_a":a["canvas_oid"],"canvas_b":b["canvas_oid"],
                    "folio_a":a["folio_label"],"folio_b":b["folio_label"],
                    "photo_source_a":a["source_yale_iiif_crop"],
                    "photo_source_b":b["source_yale_iiif_crop"],
                    "cv_proxy_class":kind,"color_appearance_label":colour,
                    "dhash_hamming_64":h,"aspect_ratio_ratio":round(ar_ratio,4),
                    "relative_image_area_sqrt_ratio":round(apparent_scale,4),
                    "unverified_possible_same_object":True,
                    "same_object_claim":"NOT_ESTABLISHED",
                    "different_perspective_claim":"NOT_TESTED",
                    "mirroring_registration":"NOT_MEASURED",
                    "3d_occlusion_consistency":"NOT_MEASURED",
                    "independent_reviewer_decision":"PENDING",
                })
    # The pre-existing HSV screen notoriously mistakes yellow parchment for
    # ochre; rank independent grayscale/darker line proposals before ochre,
    # even if yellow shapes have a dHash of zero.
    def evidence_priority(row):
        if row["color_appearance_label"] == "żółto-ochrowy":return 3
        if row["cv_proxy_class"] == "gray_outline_candidate":return 0
        if row["cv_proxy_class"] == "dark_paint_or_ink_candidate":return 1
        return 2
    for row in candidates:
        row["parchment_yellow_confound_risk"] = (
            "HIGH" if row["color_appearance_label"]=="żółto-ochrowy" else "UNKNOWN"
        )
        row["review_priority_class"] = evidence_priority(row)
    candidates.sort(key=lambda c:(c["review_priority_class"],
                                 c["dhash_hamming_64"],
                                 abs(math.log(c["aspect_ratio_ratio"])),
                                 c["roi_a"],c["roi_b"]))
    # A native-photo visual inspection showed the highest dark matches were
    # repeated black photographic corners and sheet edges. Exclude *both*
    # kinds of border-touching shapes from same-object identity ranking.
    by_id={x["id"]:x for x in rois}
    cleaned=[p for p in candidates
             if not near_photograph_border(by_id[p["roi_a"]]["source_bbox_xywh_norm"])
             and not near_photograph_border(by_id[p["roi_b"]]["source_bbox_xywh_norm"])]
    return cleaned[:limit],len(candidates),len(candidates)-len(cleaned)

def foldout_inventory(path):
    doc=json.loads(Path(path).read_text(encoding="utf-8"))
    rows=[]
    for s in doc.get("sources",[]):
        oid=str(s["canvas_oid"])
        proposals=s.get("candidate_circular_regions",[])
        rows.append({"canvas_oid":oid,"circular_hough_candidate_count":len(proposals),
                     "circle_center_normalized":[t.get("center_xy") for t in proposals],
                     "true_rosette_count":None,"ring_count":None,"sector_count":None,
                     "star_count":None,"women_count":None,"face_count":None,
                     "tower_count":None,"classification":"UNVERIFIED_MACHINE_PROPOSALS"})
    return rows

def write_tsv(path,rows):
    keys=["folio_a","folio_b","canvas_a","canvas_b","roi_a","roi_b","cv_proxy_class",
          "color_appearance_label","dhash_hamming_64","aspect_ratio_ratio",
          "relative_image_area_sqrt_ratio","same_object_claim",
          "different_perspective_claim","photo_source_a","photo_source_b"]
    with Path(path).open("w",encoding="utf-8",newline="") as fp:
        wr=csv.DictWriter(fp,fieldnames=keys,extrasaction="ignore",dialect="excel-tab")
        wr.writeheader();wr.writerows(rows)

def execute(index,cross,fold,out,tsv):
    doc,sources=load_sources(index,cross)
    rois=build_roi_records(doc,sources)
    low_color_proposals=annotate_color_absence(rois)
    pairs,total,border_rejected=find_pairs(rois)
    folds=foldout_inventory(fold)
    report={
      "schema":"voynich-exp004/multifolio-object-candidates-v1",
      "research_status":"EXPLORATORY_NOT_CONFIRMED_NO_SAME_OBJECT_IDENTIFICATION",
      "source_archive":"Yale MS408 prior EXP003 SHA-verified 206 digital JPEGs",
      "input_provenance":{
        "cv_full_sha256":hashlib.sha256(Path(index).read_bytes()).hexdigest(),
        "crosswalk_sha256":hashlib.sha256(Path(cross).read_bytes()).hexdigest(),
        "foldout_probe_sha256":hashlib.sha256(Path(fold).read_bytes()).hexdigest()},
      "scope":{
        "verified_archived_photo_count":206,"proposed_roi_count":len(rois),
        "low_color_bbox_overlap_outline_proposals":len(low_color_proposals),
        "cross_physical_group_pairs_below_dhash_threshold":total,
        "retained_ranked_pairs":len(pairs),
        "photographic_border_pairs_excluded":border_rejected,
        "human_semantic_rois_accepted":0,"different_view_object_identity_accepted":0
      },
      "semantic_attribute_registry":{k:{"status":v,"human_verified_count":None}
                                     for k,v in CATEGORIES.items()},
      "human_count_by_folio":[{"canvas_oid":str(r["canvas_oid"]),
                              "folio_label":r["folio_label"],
                              "women":None,"stars":None,"faces_orientation":None,
                              "tower_count":None,"rosette_sector_count":None,
                              "notes":"NO_INDEPENDENT_NATIVE_IMAGE_ANNOTATION"}
                             for r in doc["results"]],
      "circular_geometry_folio_proposals":folds,
      "ranked_proposed_shape_correspondences":pairs,
      "region_proposals":rois,
      "writing_and_tokens":{
          "transliteration_source":"NOT_LINKED_TO_THIS_ATLAS",
          "labels_count":None,"token_associations":None,"manuscript_deciphered":False,
          "status":"SEPARATE_EVA_OR_IVTFF_ALIGNMENT_REQUIRED"},
      "critical_guards":[
          "Image appearance classes are NOT confirmed tower, human, star, rosette or plant labels.",
          "High dHash resemblance across sections does not prove same historical object or perspective.",
          "Hashes do not normalize arbitrary rotation, skew or projection; full-resolution landmarks and graph topology required.",
          "Low overlap of digital paint ROI bboxes is NOT demonstrated intentional absence of paint.",
          "Brown-yellow appearance candidates are explicitly deprioritized because parchment may be mislabeled as ochre.",
          "Image margin/sheet-edge ROIs were excluded from identity ranking after review showed black-edge contamination. Genuine border ornaments must be annotated in a separate class.",
          "No star/woman/tower count is inferred from generic geometry.",
          "Folios with shared physical-group IDs cannot serve as independent folds.",
          "No heldout EXP001/002 data touched and same screenshot-selection data not used as independent test.",
          "No preregistered inferential p-values, bootstrap confidence intervals or FDR-tested discovery.",
      ]
    }
    Path(out).parent.mkdir(parents=True,exist_ok=True)
    Path(out).write_text(json.dumps(report,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    write_tsv(tsv,pairs)
    print("EXP004_REPORT",out,"PHOTOS",206,"ROIS",len(rois),
          "CANDIDATE_PAIRS",total,"RETAINED",len(pairs),
          "UNPAINTED_CANDIDATES",len(low_color_proposals),
          "SCIENTIFIC_VERDICT",report["research_status"],flush=True)
    for p in pairs[:8]:
        print("REVIEW_PAIR",p["folio_a"],p["folio_b"],p["dhash_hamming_64"],flush=True)
    return report

def selftest():
    assert hamming64("0"*16,"f"*16)==64
    assert hamming64("f"*16,"f"*16)==0
    assert near_photograph_border([.03,.02,.08,.04])
    assert near_photograph_border([.86,.22,.14,.45])
    assert not near_photograph_border([.2,.2,.15,.15])
    a=[.1,.2,.3,.4];b=[.2,.3,.1,.4]
    assert bbox_overlap_fraction(a,b)>.1
    r=lambda oid,g:{"canvas_oid":oid,"physical_groups":[g],"cv_proxy_class":"gray_outline_candidate",
         "hash64":"0011223344556677","color_appearance_class":"NO_COLOR_SEMANTIC_CLASSIFICATION",
         "aspect_ratio":1.0,"area_fraction":.02}
    assert not eligible_pair(r("1","Q1"),r("2","Q1"))
    assert eligible_pair(r("1","Q1"),r("2","Q2"))
    assert CATEGORIES["unpainted_deliberately"]=="NOT_INFERABLE_FROM_RGB_NONDETECTION"
    print("EXP004_SELFTEST_PASS hashlength, overlap, physical fold de-dup, unknown color semantics")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--index",default=str(INDEX))
    ap.add_argument("--crosswalk",default=str(CROSS))
    ap.add_argument("--fold",default=str(FOLD))
    ap.add_argument("--output",default=str(E4/"multifolio_object_atlas_v1.json"))
    ap.add_argument("--tsv",default=str(E4/"ranked_roi_matches_v1.tsv"))
    ap.add_argument("--selftest",action="store_true")
    args=ap.parse_args()
    if args.selftest:selftest()
    else:execute(args.index,args.crosswalk,args.fold,args.output,args.tsv)
