#!/usr/bin/env python3
"""Frozen implementation for BOUNDARY-PERIODICITY-10-vs-15-HELDOUT-01.

The script refuses to run unless all target rows are audit_status=PASS and have
native coordinates, ring_index and source SHA. It never reads Voynich text or a
historical star catalogue.
"""
from __future__ import annotations
import argparse, csv, json, math, pathlib, random
from collections import defaultdict

CALIBRATION=[('f70v1','f71r'),('f71v','f72r1')]
HELDOUT=['f72r2','f72r3','f72v1','f72v2','f72v3','f73r','f73v']
REQUIRED=['panel_id','x_native_r1','y_native_r1','ring_index','orientation_deg','visual_marker_class','connection_class','audit_status','source_sha256']

def percentile_ranks(values):
    n=len(values)
    order=sorted(range(n),key=lambda i:values[i])
    out=[0.0]*n
    for rank,i in enumerate(order): out[i]=rank/(n-1) if n>1 else 0.0
    return out

def circular_diff(a,b,period=360.0):
    d=abs(a-b)%period
    return min(d,period-d)

def panel_scores(rows):
    cx=sum(float(r['x_native_r1']) for r in rows)/len(rows)
    cy=sum(float(r['y_native_r1']) for r in rows)/len(rows)
    pts=[]
    for r in rows:
        x=float(r['x_native_r1']); y=float(r['y_native_r1'])
        # 0 degrees at page top, clockwise.
        angle=(math.degrees(math.atan2(x-cx,cy-y))+360)%360
        radius=math.hypot(x-cx,y-cy)
        pts.append((angle,radius,r))
    pts.sort(key=lambda x:x[0])
    n=len(pts)
    gaps=[]; radial=[]; ring=[]; orient=[]; klass=[]
    for i in range(n):
        a,ra,r=pts[i]; b,rb,s=pts[(i+1)%n]
        gaps.append((b-a)%360)
        radial.append(abs(rb-ra))
        ring.append(1.0 if r['ring_index']!=s['ring_index'] else 0.0)
        try: orient.append(circular_diff(float(r['orientation_deg']),float(s['orientation_deg'])))
        except ValueError: orient.append(0.0)
        klass.append(1.0 if (r['visual_marker_class'],r['connection_class'])!=(s['visual_marker_class'],s['connection_class']) else 0.0)
    comps=[percentile_ranks(x) for x in (gaps,radial,ring,orient,klass)]
    score=[sum(c[i] for c in comps)/len(comps) for i in range(n)]
    return score

def load(path):
    with path.open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
    if not rows or any(c not in rows[0] for c in REQUIRED): raise SystemExit('INVALID: missing required columns')
    by=defaultdict(list)
    for r in rows:
        if r['panel_id'] in HELDOUT or any(r['panel_id'] in pair for pair in CALIBRATION):
            if r['audit_status']!='PASS': raise SystemExit(f"BLOCKED_INCOMPLETE_ATLAS: {r['element_id']}")
            by[r['panel_id']].append(r)
    return by

def concat_pair(scores_a,scores_b): return scores_a+scores_b

def phase_score(score,period,phase):
    n=len(score)
    boundaries=[i for i in range(n) if (i+1-phase)%period==0]
    return sum(score[i] for i in boundaries)/max(1,len(boundaries))

def choose_phase(cal_scores,period):
    vals=[]
    for phase in range(period): vals.append(sum(phase_score(s,period,phase) for s in cal_scores))
    best=max(range(period),key=lambda p:vals[p])
    return best,vals[best]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('atlas',type=pathlib.Path); ap.add_argument('--out',type=pathlib.Path); ap.add_argument('--permutations',type=int,default=100000)
    a=ap.parse_args(); by=load(a.atlas)
    scores={p:panel_scores(by[p]) for p in by}
    cal=[concat_pair(scores[x],scores[y]) for x,y in CALIBRATION]
    p10,_=choose_phase(cal,10); p15,_=choose_phase(cal,15)
    obs10=sum(phase_score(scores[p],10,p10) for p in HELDOUT)
    obs15=sum(phase_score(scores[p],15,p15) for p in HELDOUT)
    rng=random.Random(30152026); null10=[]; null15=[]
    for _ in range(a.permutations):
        null10.append(sum(phase_score(scores[p],10,rng.randrange(10)) for p in HELDOUT))
        null15.append(sum(phase_score(scores[p],15,rng.randrange(15)) for p in HELDOUT))
    pval10=(1+sum(v>=obs10 for v in null10))/(1+len(null10))
    pval15=(1+sum(v>=obs15 for v in null15))/(1+len(null15))
    result={'frozen_phase_H10':p10,'frozen_phase_H15':p15,'heldout_score_H10':obs10,'heldout_score_H15':obs15,'p_perm_H10':pval10,'p_perm_H15':pval15,'seed':30152026,'permutations':a.permutations,'decision':'INCONCLUSIVE_PENDING_MDL_AND_SENSITIVITY'}
    text=json.dumps(result,indent=2,ensure_ascii=False); print(text)
    if a.out:a.out.write_text(text+'\n',encoding='utf-8')
if __name__=='__main__': main()
