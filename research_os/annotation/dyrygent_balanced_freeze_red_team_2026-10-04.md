Failed to connect to bus: Operation not permitted
# Dyrygent BALANCED red-team: annotation freeze

- Date: 2026-10-04
- Mode: `balanced`
- Preset: `research`
- Runtime: Dyrygent 3.7.0
- Model reported by Dyrygent: `gpt-6-astra`
- Usage reported: 656 input / 900 output / 1,556 total tokens, one call
- Scope: design review; the remote reviewer did not inspect local implementation or artifacts

## Verdict

The proposed checks improve integrity but, by themselves, do not prove immutable freezing, independent identity, or protection from adaptive metric disclosure. The review explicitly says not to treat a locally frozen run as an accepted blind-agreement experiment until the high-severity issues are closed.

## Findings preserved from the returned audit

1. **HIGH — validation/copy race and destination substitution.** Inputs, packets, atlas, symlinks, or the output path could change between validation and copying. The remedy is to validate and hash stable byte snapshots, reject path substitution, reserve the destination atomically without replacement, and test concurrent writers and mutation attempts.
2. **HIGH — write order is not an atomic or durable freeze.** A crash may leave incomplete artifacts, later edits remain possible, and a manifest alone is not an external commitment. The remedy is an explicit staged/committed/reported state, durable writes, digest re-verification, and an independently controlled append-only receipt.
3. **HIGH — fresh directories allow adaptive retries and selective reporting.** An operator could run many pairs and report the best. The remedy is one authoritative acceptance slot for the experiment/round/assigned annotators, preservation of every disclosed failure, and an external registry or custodian. Local directory checks cannot enforce this across machines.
4. **HIGH — distinct pseudonymous IDs are not proof of distinct annotators.** This finding was truncated in the returned response, but its heading is preserved rather than reconstructed. The implication is treated conservatively: identity independence needs an external pre-commit/custodian, not a self-asserted string comparison.

## Implemented response

- Inputs and packets are read into byte snapshots before validation; those exact bytes are hashed and stored.
- The destination is reserved with atomic `mkdir`, not `exists()` followed by replacement.
- Existing or partial run directories are never overwritten or automatically removed.
- Every artifact uses exclusive creation and is flushed; the directory is fsynced.
- `COMMIT.json` is written last and binds the manifest digest.
- Frozen files and directory are made read-only as an accidental-edit barrier.
- The manifest status is deliberately limited to `LOCAL_FREEZE_AWAITING_CUSTODIAN_RECEIPT` and declares `LOCAL_SINGLE_DIRECTORY_ONLY` acceptance scope.
- Ground-truth promotion and HELD-OUT unlocking remain false.

## Remaining external control

Before production use, register exactly one acceptance slot for `EXP-2026-001` with an independent custodian or append-only service. The receipt must bind experiment ID, annotation round, packet IDs and hashes, protocol hash, record-universe hash, precommitted annotator bindings, both submission hashes, and the freeze-manifest hash. Any later correction must supersede—never erase—the original and must be marked post-disclosure.

The unrelated Unity host action included by the generic orchestrator was ignored as out of scope.
