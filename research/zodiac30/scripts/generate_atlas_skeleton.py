#!/usr/bin/env python3
from __future__ import annotations
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTS = ROOT / 'data' / 'atlas_expected_counts.csv'
OUT = ROOT / 'data' / 'atlas_299_skeleton.csv'
COLUMNS = [
    'element_id','folio','panel_id','zodiac_role','ordinal_provisional',
    'x_native_r1','y_native_r1','x_native_r2','y_native_r2',
    'measurement_delta_px','ring_index','orientation_deg',
    'visual_marker_class','color_class','label_present','connection_class',
    'audit_status','source_sha256','source_file','object_geometry_type','notes'
]

with COUNTS.open(encoding='utf-8', newline='') as handle:
    panels = list(csv.DictReader(handle))

with OUT.open('w', encoding='utf-8', newline='') as handle:
    writer = csv.DictWriter(handle, fieldnames=COLUMNS)
    writer.writeheader()
    for row in panels:
        panel = row['panel_id']
        role = row['zodiac_role']
        count = int(row['expected_count'])
        folio = ''.join(ch for ch in panel if ch.isdigit() or ch in 'rv')
        for i in range(1, count + 1):
            writer.writerow({
                'element_id': f'{panel}-E{i:02d}',
                'folio': folio,
                'panel_id': panel,
                'zodiac_role': role,
                'ordinal_provisional': i,
                'audit_status': 'UNMEASURED',
                'object_geometry_type': 'POINT_CENTROID',
            })
print(f'Wrote {OUT}')
