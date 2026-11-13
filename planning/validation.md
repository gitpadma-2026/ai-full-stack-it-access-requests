# Requirement evidence inventory

Agent-produced evidence for human review; this does not replace the course participant's acceptance decision. Commands and observed limits are in `deliverables/verification.md`. Offline tests use frozen source facts and fake provider replies; no live accuracy or account compatibility is claimed.

## Step 1 resolution against the current spec

Status: **verified existing functionality; no application change required**. The user requested resolution without deliberately breaking a passing test. The existing-behavior rule in `planning/plan.md` applies: inspect the behavior, strengthen incomplete coverage, and record the actual result. A passing strengthened test does not require deleting working code, a fabricated failure, an empty implementation commit, or a `test Failed` message.

Commit `e99698a` (`Test first:step 1`) isolates `MockProviderTests.test_mock_provider` from storage, validation and routing, checks all 21 saved replies against the frozen scalar expectations, blocks credential/network access, and rejects unknown and changed fixture messages. The application implementation already existed before this commit. This is added regression coverage, not evidence of a new red/green implementation cycle.

| Current spec ID | Step 1 result | Evidence |
|---|---|---|
| R-96 | Verified within the offline, authored-expectation scope. | Reviewed all 252 scalar expectations in `tests/ground_truth.json` against plan rows S01–S21 and checked their evidence spans against the decoded source messages before rerunning the mock tests. No expected value was derived from application output. |
| R-137 | Verified for reproducible development examples. | T01 and T56 pass using `tests/mock_responses/`; no live model or real credential is used. |

Reverification commands and saved observations:

- `env -u API_KEY python3 -m unittest discover -s tests -k mock -v`: **2 tests passed**, saved in `planning/step-01-tests.txt`.
- `env -u API_KEY python3 -m unittest discover -s tests -v`: **38 tests passed**, saved in `planning/step-01-suite.txt`.

Step 1 is complete within this scope. No failure or implementation commit is pending for Step 1. The user retains control of committing this resolution and its logs. Subsequent steps retain the requested test-first process: any application repair must follow a genuine failing test and the user's manual commit confirmation. This resolution does not establish completion of Steps 2–8 or external submission requirements.

## Step 2 verification against the current plan

Status: **verified existing functionality; no application repair required**. The Step 2 tests were strengthened before any application change. `ExtractionTests` now owns T02–T05 and T49–T53, without storage, worker or routing dependencies; T55 remains in the starter suite with assertions for all 14 schema fields. The checks cover all 21 frozen scalar sets, every required-key omission, the planned invalid types/enums/dates, incomplete response/message status, exact quotes, field-specific missing/conflicting issues, conflicting alternatives, override evidence, corrections, new permissions, identifier mismatch and metadata-only edits. Expectations come from the plan and frozen source facts.

- `planning/step-02-tests.txt`: 9 extraction tests passed.
- `planning/step-02-suite.txt`: all 41 tests passed before Step 3 began.
- Tests and these logs were committed in `3ba8ae6` alongside Step 3's failing tests. No separate failing Step 2 result is claimed.

## Step 3 observed failure and implementation

The required ledger tests were written/refined before the repair, independently of workers and routing. `planning/step-03-tests.txt` records six passing tests and an error in T09's exact planned `provider="fake-provider-2"` subcase: `Config` rejected the identity before it could be saved. This failure was committed as `3ba8ae6` (`test Failed`) at the user's explicit request.

The subsequent application repair accepts nonempty provider identities in saved configuration, preserves their provider/model provenance, and requires an injected adapter when a worker encounters a provider other than the built-in mock/OpenAI adapters. Unknown identities fail explicitly instead of falling through to OpenAI. The CLI still offers the two built-in providers. A temporary-state check blocked credential reads and network calls and verified both explicit missing-adapter failure and successful saved-response adapter injection.

- `planning/step-03-pass.txt`: all 7 ledger tests passed after the repair; the retained starter T54 is covered by the full suite.
- `planning/step-03-suite.txt`: all 43 tests passed after the repair.
- The implementation and passing logs are awaiting the user's manual implementation commit. Steps 4–8 have not begun in this execution sequence.

## Historical inventory using the former 67-requirement mapping

The table below is retained as historical evidence. Its IDs, line references, completion count and environment observations have not been reconciled with the current 146-requirement spec; they must not be used as a current acceptance checklist. The Step 1 assessment above uses the current IDs.

| Spec line | Requirement | Met or not met | Evidence | Note |
|---|---|---|---|---|
| R-01 | Extract request_id using the schema type and allowed values. | met | tests/test_intake.py:129; planning/test-run.txt:2 | Observed passing offline check; see verification for its practical limits. |
| R-02 | Extract request_date using the schema type and allowed values. | met | tests/test_intake.py:129; planning/test-run.txt:2 | Observed passing offline check; see verification for its practical limits. |
| R-03 | Extract kind using the schema type and allowed values. | met | tests/test_intake.py:129; planning/test-run.txt:2 | Observed passing offline check; see verification for its practical limits. |
| R-04 | Extract requester using the schema type and allowed values. | met | tests/test_intake.py:129; planning/test-run.txt:2 | Observed passing offline check; see verification for its practical limits. |
| R-05 | Extract team using the schema type and allowed values. | met | tests/test_intake.py:129; planning/test-run.txt:2 | Observed passing offline check; see verification for its practical limits. |
| R-06 | Extract system using the schema type and allowed values. | met | tests/test_intake.py:129; planning/test-run.txt:2 | Observed passing offline check; see verification for its practical limits. |
| R-07 | Extract environment using the schema type and allowed values. | met | tests/test_intake.py:129; planning/test-run.txt:2 | Observed passing offline check; see verification for its practical limits. |
| R-08 | Extract permission using the schema type and allowed values. | met | tests/test_intake.py:129; planning/test-run.txt:2 | Observed passing offline check; see verification for its practical limits. |
| R-09 | Extract business_purpose using the schema type and allowed values. | met | tests/test_intake.py:129; planning/test-run.txt:2 | Observed passing offline check; see verification for its practical limits. |
| R-10 | Extract start_date using the schema type and allowed values. | met | tests/test_intake.py:129; planning/test-run.txt:2 | Observed passing offline check; see verification for its practical limits. |
| R-11 | Extract end_date using the schema type and allowed values. | met | tests/test_intake.py:129; planning/test-run.txt:2 | Observed passing offline check; see verification for its practical limits. |
| R-12 | Extract manager using the schema type and allowed values. | met | tests/test_intake.py:129; planning/test-run.txt:2 | Observed passing offline check; see verification for its practical limits. |
| R-13 | Extract supporting_quotes using the schema type and allowed values. | met | tests/test_intake.py:129; planning/test-run.txt:2 | Observed passing offline check; see verification for its practical limits. |
| R-14 | Extract issues using the schema type and allowed values. | met | tests/test_intake.py:129; planning/test-run.txt:2 | Observed passing offline check; see verification for its practical limits. |
| R-15 | Reject extra keys and missing schema properties. | met | tests/test_intake.py:133; planning/test-run.txt:18 | Observed passing offline check; see verification for its practical limits. |
| R-16 | Hash original export bytes with SHA-256 and use the filename as document_id. | met | tests/test_intake.py:71; planning/test-run.txt:3 | Observed passing offline check; see verification for its practical limits. |
| R-17 | Derive business facts only from message, not metadata. | met | tests/test_intake.py:147; planning/test-run.txt:22 | Observed passing offline check; see verification for its practical limits. |
| R-18 | Require supporting quotes to be exact decoded-message substrings. | met | tests/test_intake.py:133; planning/test-run.txt:18 | Observed passing offline check; see verification for its practical limits. |
| R-19 | Keep absent or unresolved scalar values null and identify them in issues. | met | tests/test_intake.py:155; planning/test-run.txt:23 | Observed passing offline check; see verification for its practical limits. |
| R-20 | Preserve uncorrected conflicts as null and alternatives as exact quotes. | met | tests/test_intake.py:159; planning/test-run.txt:10 | Observed passing offline check; see verification for its practical limits. |
| R-21 | Let explicit corrections replace previous values. | met | tests/test_intake.py:163; planning/test-run.txt:11 | Observed passing offline check; see verification for its practical limits. |
| R-22 | Leave relative dates unresolved. | met | tests/test_intake.py:167; planning/test-run.txt:30 | Observed passing offline check; see verification for its practical limits. |
| R-23 | For a change extract the requested new permission. | met | tests/test_intake.py:168; planning/test-run.txt:5 | Observed passing offline check; see verification for its practical limits. |
| R-24 | Keep stated request ID separate from document filename and issue mismatches. | met | tests/test_intake.py:170; planning/test-run.txt:16 | Observed passing offline check; see verification for its practical limits. |
| R-25 | Apply override rule first: review / IT Service Desk / inspect-message. | met | tests/test_intake.py:172; planning/test-run.txt:25 | Observed passing offline check; see verification for its practical limits. |
| R-26 | Route dated identified withdrawals to confirmation even with other missing facts. | met | tests/test_intake.py:177; planning/test-run.txt:35 | Observed passing offline check; see verification for its practical limits. |
| R-27 | Route other/null kind, conflicts, mismatches or missing required facts to clarification. | met | tests/test_intake.py:178; planning/test-run.txt:6 | Observed passing offline check; see verification for its practical limits. |
| R-28 | Clarify inverted date windows without swapping source values. | met | tests/test_intake.py:182; planning/test-run.txt:19 | Observed passing offline check; see verification for its practical limits. |
| R-29 | Route complete production/write/admin requests to security review. | met | tests/test_intake.py:183; planning/test-run.txt:31 | Observed passing offline check; see verification for its practical limits. |
| R-30 | Route complete staging/read requests to the system owner. | met | tests/test_intake.py:185; planning/test-run.txt:8 | Observed passing offline check; see verification for its practical limits. |
| R-31 | Never output automatic approvals or treat manager naming as approval. | met | tests/test_intake.py:129; planning/test-run.txt:2 | Observed passing offline check; see verification for its practical limits. |
| R-32 | Expose extraction failures as null extraction with actionable retry routing. | met | tests/test_intake.py:187; planning/test-run.txt:27 | Observed passing offline check; see verification for its practical limits. |
| R-33 | Preserve prior success in history when latest attempt fails. | met | tests/test_intake.py:196; planning/test-run.txt:14 | Observed passing offline check; see verification for its practical limits. |
| R-34 | Keep one current entry per document on unchanged reruns. | met | tests/test_intake.py:78; planning/test-run.txt:34 | Observed passing offline check; see verification for its practical limits. |
| R-35 | Retain earlier source versions separately when bytes change. | met | tests/test_intake.py:85; planning/test-run.txt:4 | Observed passing offline check; see verification for its practical limits. |
| R-36 | Keep credentials in environment and redact operational logs. | met | tests/test_intake.py:287; planning/test-run.txt:26 | Observed passing offline check; see verification for its practical limits. |
| R-37 | Use a language model through an implemented configurable live adapter. | met | tests/test_intake.py:287; planning/test-run.txt:26 | Observed passing offline check; see verification for its practical limits. |
| R-38 | Check response completion before using any extracted data. | met | tests/test_intake.py:133; planning/test-run.txt:18 | Observed passing offline check; see verification for its practical limits. |
| R-39 | Refresh results when relevant model, schema, prompt or policy settings change. | met | tests/test_intake.py:113; planning/test-run.txt:32 | Observed passing offline check; see verification for its practical limits. |
| R-40 | Permit operators to inspect completed work while slow work remains pending. | met | tests/test_intake.py:208; planning/test-run.txt:15 | Observed passing offline check; see verification for its practical limits. |
| R-41 | Maintain coherent shared current records under overlapping operators. | met | tests/test_intake.py:230; planning/test-run.txt:9 | Observed passing offline check; see verification for its practical limits. |
| R-42 | Resume unfinished work after an interrupted process. | met | tests/test_intake.py:241; planning/test-run.txt:28 | Observed passing offline check; see verification for its practical limits. |
| R-43 | Make current queue and extraction source versions agree. | met | tests/test_intake.py:320; planning/test-run.txt:13 | Observed passing offline check; see verification for its practical limits. |
| R-44 | Retain earlier documents when absent from later intake batches. | met | tests/test_intake.py:124; planning/test-run.txt:17 | Observed passing offline check; see verification for its practical limits. |
| R-45 | Handle malformed responses, provider errors, refusal and interruption explicitly. | met | tests/test_intake.py:133; planning/test-run.txt:18 | Observed passing offline check; see verification for its practical limits. |
| R-46 | Use mocks and require no key or network in automated tests. | met | tests/test_intake.py:63; planning/test-run.txt:24 | Observed passing offline check; see verification for its practical limits. |
| R-47 | Document workload, shared-operation and interruption assumptions and verification limits. | met | tests/test_intake.py:362; planning/test-run.txt:12 | Observed passing offline check; see verification for its practical limits. |
| R-48 | Include automated verification for a complete request. | met | tests/test_intake.py:185; planning/test-run.txt:8 | Observed passing offline check; see verification for its practical limits. |
| R-49 | Include automated verification for missing dates. | met | tests/test_intake.py:155; planning/test-run.txt:23 | Observed passing offline check; see verification for its practical limits. |
| R-50 | Include automated verification for conflicting details. | met | tests/test_intake.py:159; planning/test-run.txt:10 | Observed passing offline check; see verification for its practical limits. |
| R-51 | Include automated verification for embedded instructions. | met | tests/test_intake.py:172; planning/test-run.txt:25 | Observed passing offline check; see verification for its practical limits. |
| R-52 | Include automated verification for provider failure. | met | tests/test_intake.py:187; planning/test-run.txt:27 | Observed passing offline check; see verification for its practical limits. |
| R-53 | Include automated verification for an unchanged rerun. | met | tests/test_intake.py:78; planning/test-run.txt:34 | Observed passing offline check; see verification for its practical limits. |
| R-54 | Include automated verification for changed source content. | met | tests/test_intake.py:85; planning/test-run.txt:4 | Observed passing offline check; see verification for its practical limits. |
| R-55 | Include automated verification for a paraphrased synthetic request. | met | tests/test_intake.py:171; planning/test-run.txt:33 | Observed passing offline check; see verification for its practical limits. |
| R-56 | Include automated verification for refusal or interrupted responses. | met | tests/test_intake.py:133; planning/test-run.txt:18 | Observed passing offline check; see verification for its practical limits. |
| R-57 | Include automated verification for a failed retry after a prior success. | met | tests/test_intake.py:196; planning/test-run.txt:14 | Observed passing offline check; see verification for its practical limits. |
| R-58 | Write setup/runtime/provider/environment/intake/test/accuracy/queue instructions in README.md. | met | tests/test_intake.py:362; planning/test-run.txt:12 | Observed passing offline check; see verification for its practical limits. |
| R-59 | Supply runnable source, extraction prompt, schema, request configuration and dependency lockfile. | met | tests/test_intake.py:362; planning/test-run.txt:12 | Observed passing offline check; see verification for its practical limits. |
| R-60 | Export one extraction record with all required envelope fields per current message. | met | tests/test_intake.py:320; planning/test-run.txt:13 | Observed passing offline check; see verification for its practical limits. |
| R-61 | Export a queue linked by document_id to extraction records. | met | tests/test_intake.py:320; planning/test-run.txt:13 | Observed passing offline check; see verification for its practical limits. |
| R-62 | Write source-derived accuracy expectations for all 20 supplied messages plus one paraphrase. | met | tests/test_intake.py:335; planning/test-run.txt:1 | Observed passing offline check; see verification for its practical limits. |
| R-63 | Describe exact-match counts, denominator, factual errors, configuration and mock/live provenance. | met | tests/test_intake.py:335; planning/test-run.txt:1 | Observed passing offline check; see verification for its practical limits. |
| R-64 | Provide credential-redacted example request and implemented response handling. | met | tests/test_intake.py:287; planning/test-run.txt:26 | Observed passing offline check; see verification for its practical limits. |
| R-65 | Write verification commands, comparisons, limits and observed results in verification.md. | met | tests/test_intake.py:362; planning/test-run.txt:12 | Observed passing offline check; see verification for its practical limits. |
| R-66 | Pair coding-session capture with submitted commit. | not met | README.md; deliverables/verification.md | Entire missing; no facilitator capture or classroom per-step commit sequence. |
| R-67 | Commit and push to default branch and submit root repository URL. | not met | README.md; deliverables/verification.md | Commit/push to fork requested; Classroom link submission remains a user action. Git result is independently inspectable in history. |

Count: 65 met with the scoped evidence above; 2 not met; 67 total.

The initial missing-module failure is saved in `planning/test-first.txt`. Tests were introduced before the combined implementation, but no separate red/green commit exists for every step. Live integration is implemented and tested through fake HTTP; a live run is not inferred from passing contract tests.
