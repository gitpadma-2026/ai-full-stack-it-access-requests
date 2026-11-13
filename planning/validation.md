# Current validation and submission review

Local implementation and verification for Steps 1–8 are complete within the documented offline scope. The submission itself is **pending**: session-capture review and pairing, the final commit/push, and the Classroom receipt are not verified. This is agent-produced evidence for human review, not a claim of facilitator acceptance.

## Full-suite result

The completed command was:

```bash
env -u API_KEY python3 -m unittest discover -s tests -v
```

**56 tests passed in 50.012 seconds on Python 3.12.3.** [test-run.txt](test-run.txt) is the canonical stdout/stderr record, copied byte for byte from [remaining-suite.txt](remaining-suite.txt); this documentation update does not claim another execution. All 56 methods in the plan appear in that passing log. Tests and artifact generation use saved mock replies or fake HTTP only, with real API_KEY unset and network blocked. Credential checks patch lookup to a test sentinel. No real key or model call was used or required.

The previous 38-test canonical log is preserved as [test-run-legacy.txt](test-run-legacy.txt). Earlier step results, genuine failures and the obsolete mapping are preserved in [validation-history.md](validation-history.md), [remaining-tests-before.txt](remaining-tests-before.txt), [remaining-suite-before.txt](remaining-suite-before.txt) and [remaining-docs-before.txt](remaining-docs-before.txt). Existing passing behavior was retained; no retrospective red/green commit sequence is claimed.

## Completed local steps

| Step | Verified result | Evidence |
|---|---|---|
| 1 — mocks and source expectations | Saved responses match 21 independently authored source cases without credentials/network. | `MockProviderTests`, starter mock test, `tests/ground_truth.json` |
| 2 — extraction validation | Schema fields/types/enums/dates, completion, exact quotes, missing/conflicting facts, corrections, relative dates and identifiers checked independently of storage/routing. | `ExtractionTests`, schema starter test |
| 3 — durable revisions/settings | Original bytes and hashes, one current pointer, immutable settings, history, distinct filenames and out-of-order completion checked. Provider-identity repair committed as `2590ade`. | `LedgerTests`, source starter test |
| 4 — review routing | All 21 source routes and precedence verified independently of workers/storage. Repaired arbitrary-filename mismatches and full override evidence; mismatch annotation precedes early routing returns. | `RoutingTests`, routing failure logs |
| 5 — workers/recovery | Partial visibility, independent errors, concurrent claims/history, renewable leases/fencing, isolated-child kill/resume and service retry verified. | `IntakeTests` recovery/concurrency tests; `planning/workload.json` |
| 6 — provider/evidence | Implemented request/response adapter verified through fake HTTP; configurable payload, sentinel-only credential lookup/redaction, unseen filenames and redacted request evidence checked. | Provider, credentials, request-evidence and unseen-input tests |
| 7 — operator/export/accuracy | CLI, retries, required fields, overlapping snapshot exports, denominator cases and per-record configuration provenance checked. Engine version 2 refreshes reuse under repaired routing. | CLI/export/accuracy tests; current deliverables |
| 8 — handover/submission preparation | README, lockfile, source artifacts and documented operator commands checked. All local deliverables reviewed against CHALLENGE.md; external evidence remains pending below. | Documentation/handover tests; submission checklist |

## CHALLENGE.md and README.md submission checklist

[CHALLENGE.md](../CHALLENGE.md) is the supplied brief and was left unchanged. [README.md](../README.md) supplies setup, Python 3.10+ runtime, mock/OpenAI configuration, exact intake/test/accuracy commands, API_KEY documentation, queue inspection, history/retry/resume, and shared-operation limits. The current submission uses mocks; live execution is optional and was not performed.

| Required item | Status and inspected evidence |
|---|---|
| README.md | Ready locally: exact operator commands and runtime/provider/environment instructions are present; handover commands pass in isolated temporary state. |
| Source and dependency lock | Ready locally: `access_intake/`, `access_intake/prompt.txt`, `snapshot.schema.json`, model request construction and `requirements.lock` are present. Dependency set is empty; the provider integration is implemented and tested with fake HTTP. |
| deliverables/extractions.jsonl | Ready locally: exactly 20 supplied document IDs, required fields, original-byte SHA-256 values, schema-conforming successes, null errors and `response_source=mock` inspected. The independent paraphrase is in `deliverables/synthetic/`. |
| deliverables/queue.json | Ready locally: exact document set and shared attempt/hash/settings/routing fields agree with extractions. Snapshot checksums and top-level copies match each immutable generation. |
| deliverables/accuracy.md | Ready locally: all 20 supplied expected scalar sets plus SYN-001, exact-match procedure, 252 scalar/63 routing denominators, missing/error rules, source evidence review, factual-versus-wording distinctions, configured model/settings and mock provenance are present. Observed comparison: 252/252 scalars, 63/63 routes, no exact-match differences. This is mock-label agreement, not live accuracy. |
| deliverables/request-evidence.json | Ready locally: example body matches implemented request construction, strict schema/model/token settings are present, Authorization is redacted, completion/refusal/schema/error handling is described and `live_request_observed=false`. |
| deliverables/verification.md | Ready locally: runnable checks, intended assertions/comparisons, assumptions, observed results/repairs, configuration, mock labels and operating limits are documented. |
| Coding-session capture | Pending V01/V02: Entire enabled status alone does not prove the required facilitator-compatible session contents or a matching final commit. |
| Default-branch commit and push | Pending V03/V04: local branch and origin default-branch reference are main. The commit containing this document packages Steps 4–8 and the review at the user’s request; capture inclusion/pairing and remote push remain unverified. |
| Classroom submission | Pending V05: submit only `https://github.com/gitpadma-2026/ai-full-stack-it-access-requests`; no receipt has been verified. |

The artifact review checked required fields, schema/types/dates/quotes, input hashes, current document counts, queue agreement, snapshot checksums, request-body/redaction equality and the 252/63 comparison without network access. The user subsequently requested the commit containing this review. Push and Classroom submission were not performed; capture inclusion/pairing remains unverified.

## Current requirement coverage

All **146 current IDs** in [spec.md](spec.md) are listed below using the ownership in [plan.md](plan.md). **141 have local evidence; 5 external submission checks remain pending.** “Offline verified” means the named test passed on saved/fake data; “Inspected locally” additionally identifies repository/artifact/document review. Neither status establishes live model quality or external submission. R-135/R-136 are prepared locally and still depend on the final commit/push.

Every test reference below resolves to a passing method in `tests/test_intake.py` or `tests/test_starter.py` and [test-run.txt](test-run.txt). Source expectations and exact per-case inputs remain in the plan and `tests/ground_truth.json`.

| ID | Requirement | Step | Status | Observed test / review evidence |
|---|---|---|---|---|
| R-01 | Extract `request_id` as a string or null. | 2 | Offline verified | T02 — `test_extraction_fields` |
| R-02 | Extract `request_date` as a string or null. | 2 | Offline verified | T02 — `test_extraction_fields` |
| R-03 | Extract `kind` as a string or null; non-null values are new, change, withdrawal or other. | 2 | Offline verified | T02 — `test_extraction_fields` |
| R-04 | Extract `requester` as a string or null. | 2 | Offline verified | T02 — `test_extraction_fields` |
| R-05 | Extract `team` as a string or null. | 2 | Offline verified | T02 — `test_extraction_fields` |
| R-06 | Extract `system` as a string or null. | 2 | Offline verified | T02 — `test_extraction_fields` |
| R-07 | Extract `environment` as a string or null; non-null values are staging or production. | 2 | Offline verified | T02 — `test_extraction_fields` |
| R-08 | Extract `permission` as a string or null; non-null values are read, write or admin. | 2 | Offline verified | T02 — `test_extraction_fields` |
| R-09 | Extract `business_purpose` as a string or null. | 2 | Offline verified | T02 — `test_extraction_fields` |
| R-10 | Extract `start_date` as a string or null. | 2 | Offline verified | T02 — `test_extraction_fields` |
| R-11 | Extract `end_date` as a string or null. | 2 | Offline verified | T02 — `test_extraction_fields` |
| R-12 | Extract `manager` as a string or null. | 2 | Offline verified | T02 — `test_extraction_fields` |
| R-13 | Extract `supporting_quotes` as an array of strings. | 2 | Offline verified | T02 — `test_extraction_fields` |
| R-14 | Extract `issues` as an array of strings. | 2 | Offline verified | T02 — `test_extraction_fields` |
| R-15 | Reject extraction objects containing keys not allowed by the schema. | 2 | Offline verified | T03 — `test_invalid_outputs` |
| R-16 | Reject extraction objects missing any schema-required property. | 2 | Offline verified | T03 — `test_invalid_outputs` |
| R-17 | Use YYYY-MM-DD for extracted dates. | 2 | Offline verified | T03 — `test_invalid_outputs` |
| R-18 | Derive business facts only from message, not metadata. | 2 | Offline verified | T49 — `test_metadata_is_not_source` |
| R-19 | Require supporting quotes to be exact decoded-message substrings. | 2 | Offline verified | T03 — `test_invalid_outputs` |
| R-20 | Represent absent scalar facts as null. | 2 | Offline verified | T04 — `test_source_semantics` |
| R-21 | Represent unresolved scalar facts as null. | 2 | Offline verified | T04 — `test_source_semantics` |
| R-22 | Explain each missing fact in issues. | 2 | Offline verified | T05 — `test_evidence_and_issues` |
| R-23 | Explain each conflicting fact in issues. | 2 | Offline verified | T05 — `test_evidence_and_issues` |
| R-24 | Leave contradictory statements unresolved when no explicit correction is supplied. | 2 | Offline verified | T04 — `test_source_semantics` |
| R-25 | Preserve conflicting alternatives in exact supporting_quotes. | 2 | Offline verified | T05 — `test_evidence_and_issues` |
| R-26 | Let explicit corrections replace previous values. | 2 | Offline verified | T50 — `test_corrections` |
| R-27 | Leave relative dates unresolved. | 2 | Offline verified | T51 — `test_relative_dates` |
| R-28 | For a change extract the requested new permission. | 2 | Offline verified | T52 — `test_changes` |
| R-29 | Use the input filename as document_id. | 3 | Offline verified | T06 — `test_bytes_identity` |
| R-30 | Retain the stated request identifier when it differs from the identifier in the input filename. | 2 | Offline verified | T53 — `test_identifier` |
| R-31 | Record a mismatch between the stated request identifier and the filename identifier in issues. | 2 | Offline verified | T53 — `test_identifier` |
| R-32 | Treat each message as an independent document even when multiple messages concern one request. | 3 | Offline verified | T11 — `test_same_request_distinct_documents` |
| R-33 | Apply review-queue rules in the supplied order after validating the extraction. | 4 | Offline verified | T23 — `test_routing_precedence` |
| R-34 | Route an instruction-override attempt before applying other routing rules, with status review, owner IT Service Desk and next_action inspect-message. | 4 | Offline verified | T17 — `test_override` |
| R-35 | Route a withdrawal with request_id and request_date to status review, owner IT Service Desk and next_action confirm-withdrawal even when other facts are missing. | 4 | Offline verified | T18 — `test_withdrawal` |
| R-36 | Route a message with kind other or null, conflicting details, an identifier mismatch or any missing required fact to status needs-information, owner IT Service Desk and next_action clarify unless an earlier routing rule applies. | 4 | Offline verified | T19 — `test_clarification` |
| R-37 | Route a complete new or change request involving production, write or admin to status review, owner Security Review and next_action review-risk-then-owner. | 4 | Offline verified | T20 — `test_security` |
| R-38 | Route a complete staging/read request to status review, owner System Owner and next_action review-request. | 4 | Offline verified | T14 — `test_complete` |
| R-39 | Keep an instruction-override attempt as source evidence. | 4 | Offline verified | T17 — `test_override` |
| R-40 | Identify an instruction-override attempt in issues. | 4 | Offline verified | T17 — `test_override` |
| R-41 | Treat source messages as data throughout extraction and routing. | 6 | Offline verified | T36 — `test_provider_contract` |
| R-42 | Allow fields other than request_id and request_date to be null for withdrawal confirmation. | 4 | Offline verified | T18 — `test_withdrawal` |
| R-43 | Identify absent withdrawal facts in issues. | 4 | Offline verified | T18 — `test_withdrawal` |
| R-44 | Require request_id, request_date, requester, team, system, environment, permission, business_purpose, start_date, end_date and manager for new/change requests. | 4 | Offline verified | T23 — `test_routing_precedence` |
| R-45 | Treat a start_date after end_date as a clarification issue. | 4 | Offline verified | T21 — `test_inverted_dates` |
| R-46 | Leave the system-owner decision after Security Review examines risk and forwards its recommendation. | 4 | Offline verified | T20 — `test_security` |
| R-47 | Keep every successful intake output awaiting human review. | 4 | Offline verified | T13 — `test_all_source_cases` |
| R-48 | Treat a named manager as a contact rather than an approval. | 4 | Offline verified | T14 — `test_complete` |
| R-49 | Display each request’s status, owner and next action. | 7 | Offline verified | T41 — `test_queue_fields_and_retry` |
| R-50 | Represent an extraction failure with a null extraction, an actionable error, status error, owner IT Service Desk and next_action retry-extraction. | 5 | Offline verified | T24 — `test_provider_failure` |
| R-51 | Process messages independently so that an extraction failure leaves unaffected messages moving through intake. | 5 | Offline verified | T24 — `test_provider_failure` |
| R-52 | Make processing failures visible with a reproducible retry command. | 7 | Offline verified | T41 — `test_queue_fields_and_retry` |
| R-53 | Identify source revisions with SHA-256 hashes of the original export bytes. | 3 | Offline verified | T06 — `test_bytes_identity` |
| R-54 | Keep one current entry per document on unchanged reruns. | 3 | Offline verified | T07 — `test_unchanged` |
| R-55 | Reuse results when the source and relevant processing settings are unchanged. | 3 | Offline verified | T07 — `test_unchanged` |
| R-56 | Create a new result when input content changes. | 3 | Offline verified | T08 — `test_changed_source` |
| R-57 | Retain the earlier result with its earlier source hash when input content changes. | 3 | Offline verified | T08 — `test_changed_source` |
| R-58 | Store prior versions separately from current outputs. | 3 | Offline verified | T08 — `test_changed_source` |
| R-59 | Preserve the last valid result in history when a later attempt fails. | 5 | Offline verified | T25 — `test_failed_retry` |
| R-60 | Show the latest attempt’s error in the current queue when a later attempt fails. | 5 | Offline verified | T25 — `test_failed_retry` |
| R-61 | Identify older results as belonging to their earlier attempts and source versions when a new attempt fails. | 5 | Offline verified | T25 — `test_failed_retry` |
| R-62 | Refresh affected results when source inputs or relevant processing settings change. | 3 | Offline verified | T09 — `test_settings_refresh` |
| R-63 | Identify which settings and policy version produced the records operators use. | 3 | Offline verified | T12 — `test_saved_provenance` |
| R-64 | Keep the current view aligned with the latest processed source. | 3 | Offline verified | T12 — `test_saved_provenance` |
| R-65 | Retain earlier documents when absent from later intake batches. | 3 | Offline verified | T10 — `test_incremental_batches` |
| R-66 | Keep credentials in environment variables. | 6 | Offline verified | T37 — `test_provider_credentials_and_redaction` |
| R-67 | Redact credentials from operational logs. | 6 | Offline verified | T37 — `test_provider_credentials_and_redaction` |
| R-68 | Support the facilitator-provided API key through the environment variable API_KEY. | 6 | Offline verified | T37 — `test_provider_credentials_and_redaction` |
| R-69 | Use a language model to extract request details into records conforming to snapshot.schema.json. | 6 | Offline verified | T36 — `test_provider_contract`; fake HTTP only; live quality unverified |
| R-70 | Keep model/provider settings configurable. | 6 | Offline verified | T36 — `test_provider_contract` |
| R-71 | Document a supported model/provider configuration. | 8 | Inspected locally | T47 — `test_docs` |
| R-72 | Validate response structure before using extracted data. | 2 | Offline verified | T03 — `test_invalid_outputs` |
| R-73 | Validate response completion status before using extracted data. | 2 | Offline verified | T03 — `test_invalid_outputs` |
| R-74 | Handle malformed model output explicitly. | 5 | Offline verified | T31 — `test_refusal_and_interruption_are_current_errors` |
| R-75 | Handle provider errors explicitly. | 5 | Offline verified | T24 — `test_provider_failure` |
| R-76 | Handle model refusal explicitly. | 5 | Offline verified | T31 — `test_refusal_and_interruption_are_current_errors` |
| R-77 | Handle interrupted model responses explicitly. | 5 | Offline verified | T31 — `test_refusal_and_interruption_are_current_errors` |
| R-78 | Make completed results available for inspection while other requests remain pending. | 5 | Offline verified | T26 — `test_fast_before_slow` |
| R-79 | Maintain a coherent current queue when operators process requests concurrently. | 5 | Offline verified | T27 — `test_concurrent_claims` |
| R-80 | Maintain a trustworthy record of earlier activity when operators process requests concurrently. | 5 | Offline verified | T34 — `test_concurrent_history_audit` |
| R-81 | Distinguish completed work from unfinished work after a process interruption. | 5 | Offline verified | T32 — `test_process_interruption_resume` |
| R-82 | Resume unfinished work from recorded state after a process interruption. | 5 | Offline verified | T32 — `test_process_interruption_resume` |
| R-83 | Keep the queue and supporting extraction records in agreement about the source version. | 7 | Offline verified | T44 — `test_concurrent_export_snapshot` |
| R-84 | Resume processing after model-service interruptions without losing completed work. | 5 | Offline verified | T33 — `test_service_recovery_preserves_completed` |
| R-85 | Include automated verification for a complete request. | 4 | Offline verified | T14 — `test_complete` |
| R-86 | Include automated verification for missing dates. | 4 | Offline verified | T15 — `test_missing_dates` |
| R-87 | Include automated verification for conflicting details. | 4 | Offline verified | T16 — `test_conflicts` |
| R-88 | Include automated verification for embedded instructions. | 4 | Offline verified | T17 — `test_override` |
| R-89 | Include automated verification for provider failure. | 5 | Offline verified | T24 — `test_provider_failure` |
| R-90 | Include automated verification for an unchanged rerun. | 3 | Offline verified | T07 — `test_unchanged` |
| R-91 | Include automated verification for changed source content. | 3 | Offline verified | T08 — `test_changed_source` |
| R-92 | Add a paraphrased synthetic request to exercise extraction on fresh wording. | 4 | Offline verified | T22 — `test_synthetic` |
| R-93 | Include checks for refusal responses. | 5 | Offline verified | T31-A — `test_refusal_and_interruption_are_current_errors` |
| R-94 | Include checks for interrupted responses. | 5 | Offline verified | T31-B — `test_refusal_and_interruption_are_current_errors` |
| R-95 | Include automated verification for a failed retry after a prior success. | 5 | Offline verified | T25 — `test_failed_retry` |
| R-96 | Specify expected facts from the source messages and policy independently of the extraction outputs being measured. | 1 | Inspected locally | T01 — `test_mock_provider` |
| R-97 | Describe how the implementation supports the operating context. | 8 | Inspected locally | T47 — `test_docs` |
| R-98 | Include checks for the operational situations the design handles. | 5 | Offline verified | T35 — `test_offline_burst` |
| R-99 | Record workload assumptions. | 8 | Inspected locally | T47 — `test_docs` |
| R-100 | Record shared-operation assumptions. | 8 | Inspected locally | T47 — `test_docs` |
| R-101 | Record expected behavior during interruptions. | 8 | Inspected locally | T47 — `test_docs` |
| R-102 | Record the limits of the verification performed. | 8 | Inspected locally | T47 — `test_docs` |
| R-103 | Provide README.md with setup instructions. | 8 | Inspected locally | T47 — `test_docs` |
| R-104 | Document the supported runtime and provider in README.md. | 8 | Inspected locally | T47 — `test_docs` |
| R-105 | Document the exact intake command in README.md. | 8 | Inspected locally | T47 — `test_docs` |
| R-106 | Document the exact test command in README.md. | 8 | Inspected locally | T47 — `test_docs` |
| R-107 | Document the exact accuracy-check command in README.md. | 7 | Inspected locally | T46 — `test_accuracy_report` |
| R-108 | Document environment-variable names in README.md. | 8 | Inspected locally | T47 — `test_docs` |
| R-109 | Document how to inspect the queue in README.md. | 8 | Inspected locally | T47 — `test_docs` |
| R-110 | Provide runnable application source code. | 7 | Inspected locally | T40 — `test_cli` |
| R-111 | Provide a dependency lockfile. | 8 | Inspected locally | T47 — `test_docs` |
| R-112 | Provide the extraction prompt. | 6 | Inspected locally | T36 — `test_provider_contract` |
| R-113 | Provide the extraction schema. | 2 | Inspected locally | T02 — `test_extraction_fields` |
| R-114 | Provide the model request configuration. | 6 | Inspected locally | T36 — `test_provider_contract` |
| R-115 | Provide deliverables/extractions.jsonl with one current record per message containing document_id, source_sha256, extraction, status, owner, next_action, error and response_source. | 7 | Inspected locally | T43 — `test_export_required_fields` |
| R-116 | Use a schema-conforming extraction object on success and null on error in deliverables/extractions.jsonl. | 7 | Inspected locally | T43 — `test_export_required_fields` |
| R-117 | Set error to null on success in deliverables/extractions.jsonl. | 7 | Inspected locally | T43 — `test_export_required_fields` |
| R-118 | Label each extraction record with response_source identifying mock output or the provider and model ID that produced it. | 7 | Inspected locally | T43 — `test_export_required_fields` |
| R-119 | Provide deliverables/queue.json with the review queue linked to extraction records by document_id. | 7 | Inspected locally | T42 — `test_export` |
| R-120 | Provide deliverables/accuracy.md with source-derived expected fields for all 20 supplied messages. | 7 | Inspected locally | T46 — `test_accuracy_report` |
| R-121 | Include source-derived expected fields for one authored paraphrase in deliverables/accuracy.md. | 7 | Inspected locally | T46 — `test_accuracy_report` |
| R-122 | Document the field-comparison procedure in deliverables/accuracy.md. | 7 | Inspected locally | T46 — `test_accuracy_report` |
| R-123 | Document exact-match counting and denominator rules in deliverables/accuracy.md. | 7 | Inspected locally | T46 — `test_accuracy_report` |
| R-124 | Include factual-error reporting in deliverables/accuracy.md. | 7 | Inspected locally | T46 — `test_accuracy_report` |
| R-125 | Identify the model and configuration in deliverables/accuracy.md. | 7 | Inspected locally | T46 — `test_accuracy_report` |
| R-126 | Distinguish mocked examples from optional live observations in deliverables/accuracy.md. | 7 | Inspected locally | T46 — `test_accuracy_report` |
| R-127 | Provide deliverables/request-evidence.json with a credential-redacted example model request showing the model ID and configuration used. | 6 | Inspected locally | T38 — `test_request_evidence` |
| R-128 | Include the implemented response handling in deliverables/request-evidence.json. | 6 | Inspected locally | T38 — `test_request_evidence` |
| R-129 | Provide deliverables/verification.md with verification commands and assertions. | 8 | Inspected locally | T47 — `test_docs` |
| R-130 | Document the intended verification comparisons in deliverables/verification.md. | 8 | Inspected locally | T47 — `test_docs` |
| R-131 | Document operating limits in deliverables/verification.md. | 8 | Inspected locally | T47 — `test_docs` |
| R-132 | Clearly identify any observed results or repairs in deliverables/verification.md. | 8 | Inspected locally | T47 — `test_docs` |
| R-133 | Provide coding-session capture collected through the facilitator’s capture setup. | 8 — prepare submission evidence | Pending external evidence | V01 — facilitator capture artifact not inspected |
| R-134 | Pair the submitted commit with its coding-session capture. | 8 — prepare submission evidence | Pending external evidence | V02 — final commit/capture pairing not inspected |
| R-135 | Submit the implemented provider integration. | 6 | Ready locally; submission pending | T36 — `test_provider_contract`; final commit/push pending |
| R-136 | Submit the source-grounded validation procedure. | 7 | Ready locally; submission pending | T46 — `test_accuracy_report`; final commit/push pending |
| R-137 | Use mocked responses for reproducible development examples. | 1 | Offline verified | T01 — `test_mock_provider` |
| R-138 | Label each recorded observation with its configuration and whether it used a mock or provider response. | 8 | Inspected locally | T47 — `test_docs` |
| R-139 | Commit the application, outputs and session capture to the repository’s default branch. | 8 — prepare submission evidence | Pending external evidence | V03 — verify this commit includes facilitator-compatible capture on main |
| R-140 | Push the application, outputs and session capture to the repository’s remote default branch. | 8 — prepare submission evidence | Pending external evidence | V04 — final changes have not been pushed |
| R-141 | Submit only the root repository link through the Classroom assignment. | 8 — prepare submission evidence | Pending external evidence | V05 — Classroom receipt not supplied |
| R-142 | Provide a documented interface for operators to start intake. | 8 | Inspected locally | T48 — `test_handover_commands` |
| R-143 | Accept other request messages in the same export format beyond the supplied sample. | 6 | Offline verified | T39 — `test_unseen_provider_input`; fake HTTP only; live quality unverified |
| R-144 | Read each input export as a UTF-8 JSON document containing one message. | 3 | Inspected locally | T06 — `test_bytes_identity` |
| R-145 | Document how operators inspect completed results while other requests are pending. | 8 | Inspected locally | T48 — `test_handover_commands` |
| R-146 | Document how operators resume unfinished work. | 8 | Inspected locally | T48 — `test_handover_commands` |

## Verification limits and remaining submission actions

The four-worker/2,000-document benchmark completed with 2,000 claims, 2,000 terminal records, zero extraction errors and 2,000 deliberate filename-mismatch clarifications. Exact timings and peak active mock calls are in `planning/workload.json`; no latency SLA or live throughput claim is made. SQLite sharing is limited to one host and one local database. Remote calls may be repeated after interruption; pacing is per process, retention is not automatic, and semantic correctness still requires source review. The isolated-child recovery test does not simulate a real host power cut.

To complete submission, inspect the facilitator-compatible capture artifact, pair it with the final commit, commit the application/outputs/capture on main, push that commit to the remote default branch and verify the remote tip, then retain the Classroom receipt containing only the root repository URL. These are pending actions, not passed tests. A live model call or real API key is unnecessary for this mocked submission.
