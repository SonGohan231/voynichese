#!/usr/bin/env python3
"""Batch visual inventory for Voynich MS408 — computational candidates, never semantic proof.

Inputs: Yale archival JPEGs already preserved on the separate archive branch
and verified source ledger. Outputs are measured pixel-color masks, geometry
ROI and perceptual-hash similarities. NO plant species, tower semantics, fold
geometry, historical depth or original reading order is inferred.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "EXP-2026-002"
ARCHIVE = EXPERIMENT / "yale_archived_jpeg_provenance_crosswalk_2026-10-09.json"
BRANCH = "import-voynich-yale-scans-2026-07-23"
REPO = "SonGohan231/voynichese"
COLOR_BINS = ("niebieski", "zielony", "czerwony", "żółto-ochrowy", "ciemne_linie")
MAX_BYTES = 55_000_000
WORK_SIZE = 960


def fetch_image(entry):
    path = entry["path"]
    if not path.startswith("data/yale_hq_scans/") or ".." in path.split("/"):
        raise ValueError("Invalid archive path")
    url = "https://raw.githubusercontent.com/{}/{}/{}".format(
        REPO, BRANCH, urllib.parse.quote(path, safe="/")
    )
    req = urllib.request.Request(url, headers={
        "User-Agent": "VoynichComputerVisionInventory/1.0 (+https://github.com/SonGohan231/voynichese)"
    })
    exc = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=130) as f:
                data = f.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise ValueError("File exceeds safety cap")
            sha = hashlib.sha256(data).hexdigest()
            if sha != entry["imported_reported_sha256"]:
                raise ValueError("SHA-256 mismatch against verified source ledger")
            im = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            if im is None:
                raise ValueError("JPEG decode failed")
            return im
        except Exception as err:
            exc = err
            if attempt < 3:
                time.sleep(2 + attempt * 3)
    raise RuntimeError("{}: {}".format(path, exc))


def resize_photo(im):
    h, w = im.shape[:2]
    scale = min(1, WORK_SIZE / max(w, h))
    if scale < 1:
        return cv2.resize(im, (max(1, round(w * scale)), max(1, round(h * scale))),
                          interpolation=cv2.INTER_AREA)
    return im.copy()


def describe_region(mask, contour, im, oid, class_name, index):
    h, w = im.shape[:2]
    x, y, ww, hh = cv2.boundingRect(contour)
    area = cv2.contourArea(contour)
    if ww < 9 or hh < 9 or area <= 10:
        return None
    if area / (w * h) < 0.00023 or area / (w * h) > 0.38:
        return None
    ar = ww / max(1, hh)
    if ar > 21 or ar < 1 / 21:
        return None
    crop = cv2.cvtColor(im[y:y+hh, x:x+ww], cv2.COLOR_BGR2GRAY)
    crop = cv2.resize(crop, (9, 8), interpolation=cv2.INTER_AREA)
    hsh = 0
    for p in (crop[:, 1:] > crop[:, :-1]).ravel():
        hsh = (hsh << 1) | int(p)
    moments = cv2.moments(contour)
    color = im[y:y+hh, x:x+ww].mean(axis=(0,1))[::-1]
    return {
        "id": "{}-{}-{}".format(oid, class_name, index),
        "canvas_oid": oid, "label_type": class_name,
        "region_status": "UNVERIFIED_COMPUTER_VISION_CANDIDATE",
        "bbox_normalized_xywh": [round(x/w,5),round(y/h,5),round(ww/w,5),round(hh/h,5)],
        "area_fraction": round(float(area/(w*h)),6),
        "aspect_ratio": round(ar,4),
        "mean_rgb": [round(float(v),1) for v in color],
        "dhash64": "{:016x}".format(hsh),
        "semantic_identity": "UNKNOWN",
        "human_reviewed": False,
    }


def classify_pixel_masks(im):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    h = hsv[:,:,0]
    s = hsv[:,:,1]
    v = hsv[:,:,2]
    # Empirical thresholds classify image pixel appearance, NOT chemical pigments.
    blue = (h >= 91) & (h <= 136) & (s >= 46) & (v >= 42)
    green = (h >= 30) & (h < 91) & (s >= 43) & (v >= 38)
    red = ((h <= 11) | (h >= 170)) & (s >= 65) & (v >= 40) & (v < 245)
    ochre = (h >= 11) & (h <= 40) & (s >= 42) & (v >= 46) & (v < 229)
    ink = (v <= 103) & (s <= 165)
    # Colored classes disjoint, to count each visible pixel once.
    blue &= ~ink
    green &= ~ink & ~blue
    red &= ~ink & ~blue & ~green
    ochre &= ~ink & ~blue & ~green & ~red
    return dict(zip(COLOR_BINS, (blue, green, red, ochre, ink)))


def contours_from_masks(im, oid, masks):
    h, w = im.shape[:2]
    regions = []
    for cname in COLOR_BINS:
        bit = (masks[cname].astype(np.uint8) * 255)
        kernel = np.ones((3,3),np.uint8)
        bit = cv2.morphologyEx(bit, cv2.MORPH_OPEN, kernel)
        shapes,_ = cv2.findContours(bit, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        shapes = sorted(shapes,key=cv2.contourArea,reverse=True)[:45]
        found = 0
        for contour in shapes:
            item = describe_region(bit,contour,im,oid,"barwa_"+cname,found)
            if item is not None:
                regions.append(item);found += 1
            if found>=12:break
    # Geometry candidates: circles, elongated structures and arbitrary contours;
    # do NOT call tall rectangles "towers" or round structures "rosettes".
    gray = cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray,(5,5),0),55,135)
    shapes,_=cv2.findContours(edges,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    shapes=sorted(shapes,key=cv2.contourArea,reverse=True)[:180]
    counters=defaultdict(int)
    for contour in shapes:
        area=cv2.contourArea(contour)
        if area < w*h*0.0015 or area > w*h*0.25:continue
        perimeter=cv2.arcLength(contour,True)
        if perimeter <=0:continue
        x,y,cw,ch=cv2.boundingRect(contour)
        circularity=4*np.pi*area/(perimeter*perimeter)
        aspect=cw/max(ch,1)
        if circularity>=0.60 and .59<=aspect<=1.65:
            cname="kontur_kolisty_kandydat"
        elif aspect<.36 or aspect>2.9:
            cname="kontur_wydłużony_kandydat"
        else:
            cname="kontur_nieregularny_kandydat"
        if counters[cname]>=8:continue
        reg=describe_region(edges,contour,im,oid,cname,counters[cname])
        if reg:
            reg["roundness"] = round(float(circularity),4)
            regions.append(reg);counters[cname]+=1
    return regions


def find_crossfolio_matches(entries, max_pairs=180):
    # Exhaustive low-dimensional candidate search across different photo canvases.
    # Similar phash may be common geometry, background or scanning artefacts.
    nodes=[]
    for row in entries:
        for roi in row["rois"]:
            if roi["label_type"] == "barwa_ciemne_linie":continue
            nodes.append(roi)
    buckets=defaultdict(list)
    for roi in nodes:buckets[roi["label_type"]].append(roi)
    matches=[]
    for label,group in buckets.items():
        for i,left in enumerate(group):
            code=int(left["dhash64"],16)
            for right in group[i+1:]:
                if left["canvas_oid"]==right["canvas_oid"]:continue
                ratio=left["aspect_ratio"]/max(.01,right["aspect_ratio"])
                if ratio<.45 or ratio>2.22:continue
                diff=(code^int(right["dhash64"],16)).bit_count()
                if diff>7:continue
                a=left["area_fraction"]/max(1e-7,right["area_fraction"])
                if a<.25 or a>4:continue
                matches.append({
                    "region_a":left["id"],"region_b":right["id"],
                    "canvas_a":left["canvas_oid"],"canvas_b":right["canvas_oid"],
                    "label_type":label,"perceptual_hash_hamming":diff,
                    "status":"UNVERIFIED_SHAPE_SIMILARITY_ONLY",
                    "semantic_equivalence":"UNKNOWN",
                    "human_reviewed":False
                })
    matches.sort(key=lambda t:(t["perceptual_hash_hamming"],t["canvas_a"],t["canvas_b"]))
    return matches[:max_pairs],len(matches)


def build(archive_file,output,summary_file):
    archive=json.loads(archive_file.read_text())
    seen=set()
    selected=[]
    for entry in archive["archive_files"]:
        if entry["canvas_oid"] in seen:continue
        seen.add(entry["canvas_oid"]);selected.append(entry)
    if len(selected)!=206:raise ValueError("Expected 206 unique Yale image canvases")
    rows=[]
    failures=[]
    for index,entry in enumerate(selected,1):
        oid=entry["canvas_oid"]
        try:
            original=fetch_image(entry)
            original_size=list(original.shape[:2][::-1])
            im=resize_photo(original)
            del original
            masks=classify_pixel_masks(im)
            denom=im.shape[0]*im.shape[1]
            percentages={color:round(100*int(np.count_nonzero(m))/denom,3)
                         for color,m in masks.items()}
            unclassified=100-sum(percentages.values())
            percentages["nieoznaczone_pergamin_inne"]=round(unclassified,3)
            rois=contours_from_masks(im,oid,masks)
            rows.append({
                "canvas_oid":oid,"folio_label":entry["yale_label"],
                "physical_group_ids":entry["physical_group_ids"],
                "source_path":entry["path"],
                "jpeg_sha256_recomputed_match":True,
                "source_dimensions":original_size,
                "processing_dimensions":list(im.shape[:2][::-1]),
                "color_appearance_percent_of_pixels":percentages,
                "roi_candidates":len(rois),"rois":rois,
                "pigment_composition":"NOT_MEASURED_FROM_PIXELS",
                "plant_parts":"NOT_SEMANTICALLY_CLASSIFIED",
                "towers":"NOT_SEMANTICALLY_CLASSIFIED",
                "perspective_depth":"NOT_INFERRED"
            })
            if index%20==0 or index==206:
                print("[{}/206] {} ({} ROI candidates)".format(index,entry["yale_label"],len(rois)),flush=True)
        except Exception as exc:
            failures.append({"index":index,"oid":oid,"path":entry["path"],"error":str(exc)})
            print("[{}/206] FAILED {}".format(index,entry["yale_label"]),flush=True)
    matches,rawmatches=find_crossfolio_matches(rows)
    totals=defaultdict(list)
    for r in rows:
        for k,v in r["color_appearance_percent_of_pixels"].items():
            totals[k].append(v)
    avg={k:round(sum(v)/len(v),3) for k,v in totals.items()}
    report={
        "schema":"exp-2026-003/yale-cv-pixel-appearance-v1",
        "generated_utc":__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "status":"AUTOMATED_IMAGE_MEASUREMENTS_NOT_HUMAN_REVIEW",
        "provenance":"GitHub archival JPEG branch; JPEG bytes verified against historical SHA256 during this run",
        "scope":{
            "yale_manifest_total":213,"archived_unique_images_expected":206,
            "archived_image_entries":207,"images_processed":len(rows),"failed":len(failures),
            "image_level_pixel_color_measurements":len(rows),
            "computer_generated_roi_candidates":sum(len(x["rois"]) for x in rows),
            "cross_image_matches_all_before_limit":rawmatches,
            "cross_image_matches_retained":len(matches),
            "manuscript_parts_human_labelled":0
        },
        "method":{
            "image_resize_max_side_px":WORK_SIZE,
            "color":"OpenCV HSV hand-set thresholds of JPEG pixels incl. blue, green, red, yellow/ochre and dark, without parchment/color calibration",
            "regions":"OpenCV connected-component contours and Canny edges, normalized bounding boxes with dHash64 descriptors",
            "similarity":"cross-canvas perceptual dHash <=7 with aspect and area filters; similarity is NOT object identity",
            "2point5d":"NOT_A_DEPTH_RECONSTRUCTION; only 2D shape proposals",
            "confidence":"No model accuracy established; every machine ROI and match requires independent human assessment"
        },
        "average_color_percentages_across_images":avg,
        "results":rows,
        "candidate_shape_pairs":matches,
        "failures":failures,
        "historical_original_order":"UNKNOWN",
        "science_status":"INCONCLUSIVE_NOT_RUN",
        "held_out_exp2026001_exposed":False
    }
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,separators=(",",":"))+"\n")
    subset={
        "schema":report["schema"],"generated_utc":report["generated_utc"],
        "status":report["status"],"scope":report["scope"],
        "average_color_percentages_across_images":avg,
        "results":[{k:v for k,v in r.items() if k in ("canvas_oid","folio_label","physical_group_ids","source_path","source_dimensions","color_appearance_percent_of_pixels","roi_candidates","rois")} for r in rows],
        "candidate_shape_pairs":matches,
        "uncertainty":{
          "semantic_objects":"UNKNOWN_NOT_HUMAN_REVIEWED",
          "pigment_chemistry":"NO_CHEMISTRY_FROM_DIGITAL_PIXELS",
          "2point5d_depth":"NO_DEPTH_INFORMATION_MEASURED",
          "original_order":"UNKNOWN"
        },
        "science_status":"INCONCLUSIVE_NOT_RUN"
    }
    summary_file.write_text(json.dumps(subset,ensure_ascii=False,separators=(",",":"))+"\n")
    print(json.dumps(report["scope"],ensure_ascii=False),flush=True)
    if failures:
        raise RuntimeError("{} failed images; see JSON receipt".format(len(failures)))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--summary",type=Path,required=True)
    arguments=parser.parse_args()
    build(ARCHIVE,arguments.output,arguments.summary)
