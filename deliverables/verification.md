# Verification and operating limits

## Reproducible commands and comparisons

Run these from the repository root:

```bash
env -u API_KEY python3 -m unittest discover -s tests -v
python3 -m access_intake intake materials/requests
python3 -m access_intake queue --json
python3 -m access_intake export --out deliverables
python3 -m access_intake --db .state/synthetic.db intake examples/requests
python3 -m access_intake --db .state/synthetic.db export --out deliverables/synthetic
python3 -m access_intake accuracy
python3 -m access_intake request-evidence
python3 tools/benchmark_intake.py --count 2000 --workers 4 --out planning/workload.json
python3 tools/check_prerequisites.py
```

- Automated suite: see `planning/test-run.txt` for observed case names/results. Tests use source-grounded expectations saved before application implementation and mocks/fake HTTP only, without API_KEY. No live model was called.
- All supplied examples plus the paraphrase: compare 12 frozen scalar fields per message to saved replies and routing to the five ordered policy rules; quotes are verified against the decoded source. Exact expected spans, null cases and evidence are in `tests/ground_truth.json` and `planning/plan.md`.
- Recovery: tests expire and reclaim a lease, reject a stale completion, renew a live lease, retain earlier success when the latest attempt fails, and prevent an older source's completion from replacing the latest attempt. This exercises database recovery/fencing; no actual machine power cut is simulated.
- Shared operation: two subprocesses resume one database concurrently. Assert exactly 20 claims/completed records and no duplicates. A separate blocked-provider test asserts a fast result becomes inspectable while a slow one remains running. SQLite is tested on one host only.
- Revision/reuse: unchanged rerun creates no new attempt; byte-only JSON changes create a new hash/result/history record; a subsequent explicit read-to-write source edit changes the current permission and security routing while retaining the earlier read result; model, prompt, policy and schema changes invalidate reuse. A partial batch preserves previously ingested documents.
- Failures: provider exceptions, malformed exports, refusals, interrupted outputs, malformed JSON, extra/missing fields, bad scalar/array types, invalid enum/calendar dates and invented quotes fail explicitly. Failed outputs have null extraction and retry routing.
- Provider contract: fake HTTP asserts model/schema/store/request format, explicit authentication header isolation, retry on 429/timeouts, bounded calls, no retry on 401 and credential-safe error messages. It does not establish account model access or real API compatibility through a live call. Numeric Retry-After is supported; HTTP-date Retry-After falls back to bounded backoff.
- Export: compare document_id, attempt_id, source hash and routing across linked files. An immutable generation plus checksum manifest enables consistent reads during overlapping export; root copies alone do not provide an atomic multi-file read.
- Accuracy: observed mock scalar matches 252/252 and routing matches 63/63 with zero exact-match differences. This is agreement with authored mock labels, not live quality evidence. Source quote selection/issue prose is not included in the denominator. Factual error classification still requires human comparison to original messages.

## Observed workload

`planning/workload.json` records a 2,000-document smoke run with four workers on Python 3.12.3. It completed 2,000 records with exactly 2,000 claims and zero errors. Enqueue took 11.065 seconds and processing took 10.655 seconds on this environment. Each input deliberately repeats IT-001's known message under an independent filename; the provider replays IT-001's saved reply. This measures scheduling, durable writes, validation and routing for repeated mock data. It does not measure semantic generalization, production latency, provider quota behavior or multi-host scaling.

## Observations and repairs

Step 1 was subsequently resolved as verified existing functionality at the user's request, without deliberately breaking passing tests. Commit `e99698a` adds isolated mock-provider regression coverage to an implementation that already existed; it does not demonstrate a fresh failing-test/implementation cycle. All 252 frozen scalar expectations were checked against plan rows S01–S21, and source evidence spans were checked against the original messages before mock execution. The two Step 1 tests pass (`planning/step-01-tests.txt`), and the full offline suite passes all 38 tests (`planning/step-01-suite.txt`). No Step 1 application repair, failing-test commit or empty implementation commit is needed. See `planning/validation.md` for the scoped R-96/R-137 assessment. Later implementation repairs still require genuine failing tests and the user's manual commit confirmation.

`planning/test-first.txt` records the initial combined pre-implementation run: the starter tests passed, and importing the new application tests failed because the module did not exist. An intermediate suite run had 34 passing cases and one failure for missing deliverable documentation. The handover documents and deliverables were then created, and the complete suite was rerun. This record does not claim a separate failing test/code commit for every step. The final saved run records 38 passing tests on Python 3.12.3.

The application uses local SQLite WAL, short write transactions, immutable attempt settings, leases/heartbeats and fencing. It supports at-least-once remote calls after interruption, not exactly-once billing. Live start pacing is per process, so operators must coordinate the shared quota. Different source revisions are ordered by intake transaction, not exported_at. Histories and snapshot generations have no automatic retention/pruning. Policy rules are implemented in the deterministic router; changed business rules require code/test updates before refreshed routing is trusted.

No load test against a live provider, exhaustive injection defense test, real host-crash test, cross-host deployment test, long-duration disk-failure test or live-model accuracy evaluation was performed. Source-derived mocks verify the application pipeline and response handling; they do not prove that an unseen model response has extracted the correct meaning. Exact supporting quotes provide evidence to inspect, not proof that every scalar is semantically supported.

## Outstanding course/submission requirements

The prerequisite checker passes Codex, clone integrity and offline starter tests but fails session capture because `entire` is not installed. The facilitator must supply/enable the capture setup. No retrospective capture or per-step classroom commit history is claimed. Git commit/push is performed separately when the environment permits it; Classroom root-link submission is the user's final action. `planning/validation.md` inventories requirement evidence and outstanding work for human review.
