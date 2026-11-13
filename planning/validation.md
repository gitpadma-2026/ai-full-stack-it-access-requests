# Requirement evidence inventory

Agent-produced evidence for human review; this does not replace the course participant's acceptance decision. Commands and observed limits are in `deliverables/verification.md`. Offline tests use frozen source facts and fake provider replies; no live accuracy or account compatibility is claimed.

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
