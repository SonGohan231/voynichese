# HANDOFF_PACKET

- state: `BLOCKED_INCOMPLETE_ATLAS`
- active preparatory task: complete and audit `data/atlas_299_skeleton.csv`
- frozen next experiment: `BOUNDARY-PERIODICITY-10-vs-15-HELDOUT-01`
- source images: `data/yale_hq_scans/8/0127–0134`
- canonical page records: `atlas/records/0127–0134*.annotation.json`
- exact expected total: 299 peripheral elements
- excluded from denominator: 4 additional central figures
- calibration: Aries and Taurus split halves
- held-out: f72r2, f72r3, f72v1, f72v2, f72v3, f73r, f73v
- stress test: f70v2 = 29
- prohibited reruns: common 30×12° grid, one-star-one-entry, global brightness threshold
- historical source registry: `HISTORICAL_SOURCE_REGISTRY.csv`
- validator: `scripts/validate_atlas_gate.py`
- execution script: `scripts/test_boundary_periodicity.py`
- decision protocol: uploaded skill under `skill/`
