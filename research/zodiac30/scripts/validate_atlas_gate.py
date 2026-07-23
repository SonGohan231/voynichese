#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json, math, pathlib

EXPECTED={
'f70v2':29,'f70v1':15,'f71r':15,'f71v':15,'f72r1':15,
'f72r2':30,'f72r3':30,'f72v1':30,'f72v2':30,'f72v3':30,'f73r':30,'f73v':30,
}
REQUIRED=['element_id','panel_id','x_native_r1','y_native_r1','x_native_r2','y_native_r2','measurement_delta_px','ring_index','audit_status','source_sha256','source_file']


def finite_number(value: str) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def validate(path: pathlib.Path, max_delta: float) -> dict:
    errors=[]; warnings=[]
    with path.open(encoding='utf-8',newline='') as handle:
        rows=list(csv.DictReader(handle))
    missing_cols=[c for c in REQUIRED if c not in (rows[0].keys() if rows else [])]
    if missing_cols: errors.append(f'Missing columns: {missing_cols}')
    counts={k:0 for k in EXPECTED}; ids=set()
    for line,row in enumerate(rows,start=2):
        eid=row.get('element_id','')
        if not eid: errors.append(f'line {line}: missing element_id')
        elif eid in ids: errors.append(f'line {line}: duplicate element_id {eid}')
        ids.add(eid)
        panel=row.get('panel_id','')
        if panel not in EXPECTED: errors.append(f'line {line}: unexpected panel_id {panel!r}')
        else: counts[panel]+=1
        for c in ['x_native_r1','y_native_r1','x_native_r2','y_native_r2','measurement_delta_px']:
            if not finite_number(row.get(c,'')): errors.append(f'line {line}: {c} is not numeric')
        if finite_number(row.get('measurement_delta_px','')) and float(row['measurement_delta_px'])>max_delta:
            errors.append(f'line {line}: measurement_delta_px exceeds {max_delta}')
        try:
            if int(row.get('ring_index',''))<0: raise ValueError
        except ValueError: errors.append(f'line {line}: invalid ring_index')
        if row.get('audit_status')!='PASS': errors.append(f'line {line}: audit_status must be PASS')
        sha=row.get('source_sha256','')
        if len(sha)!=64 or any(ch not in '0123456789abcdef' for ch in sha): errors.append(f'line {line}: invalid source_sha256')
        if not row.get('source_file'): errors.append(f'line {line}: missing source_file')
    for panel,expected in EXPECTED.items():
        if counts[panel]!=expected: errors.append(f'{panel}: expected {expected}, got {counts[panel]}')
    if len(rows)!=299: errors.append(f'Expected 299 rows, got {len(rows)}')
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    return {'status':'PASS' if not errors else 'BLOCKED_INCOMPLETE_ATLAS','row_count':len(rows),'counts':counts,'sha256':digest,'error_count':len(errors),'warning_count':len(warnings),'errors':errors,'warnings':warnings}


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('atlas',type=pathlib.Path)
    ap.add_argument('--max-delta-px',type=float,default=8.0)
    ap.add_argument('--json-out',type=pathlib.Path)
    ap.add_argument('--max-errors',type=int,default=25)
    args=ap.parse_args()
    result=validate(args.atlas,args.max_delta_px)
    if len(result['errors']) > args.max_errors:
        result['errors_total'] = len(result['errors'])
        result['errors'] = result['errors'][:args.max_errors]
        result['errors_truncated'] = True
    text=json.dumps(result,indent=2,ensure_ascii=False)
    print(text)
    if args.json_out: args.json_out.write_text(text+'\n',encoding='utf-8')
    return 0 if result['status']=='PASS' else 2

if __name__=='__main__':
    raise SystemExit(main())
