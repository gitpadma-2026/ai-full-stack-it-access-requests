# Source-derived specification

Reviewed against all required course documents and all 20 exports. Planning began with a failed readiness gate: Entire is unavailable. The user subsequently explicitly requested implementation; the capture and Git submission requirements remain unmet until completed externally. No new business rule is inferred from this limitation.

| ID | Requirement | Source (exact quote) | Check |
|---|---|---|---|
| R-01 | Extract request_id using the schema type and allowed values. | snapshot.schema.json: “"request_id"” | test_all_source_cases |
| R-02 | Extract request_date using the schema type and allowed values. | snapshot.schema.json: “"request_date"” | test_all_source_cases |
| R-03 | Extract kind using the schema type and allowed values. | snapshot.schema.json: “"kind"” | test_all_source_cases |
| R-04 | Extract requester using the schema type and allowed values. | snapshot.schema.json: “"requester"” | test_all_source_cases |
| R-05 | Extract team using the schema type and allowed values. | snapshot.schema.json: “"team"” | test_all_source_cases |
| R-06 | Extract system using the schema type and allowed values. | snapshot.schema.json: “"system"” | test_all_source_cases |
| R-07 | Extract environment using the schema type and allowed values. | snapshot.schema.json: “"environment"” | test_all_source_cases |
| R-08 | Extract permission using the schema type and allowed values. | snapshot.schema.json: “"permission"” | test_all_source_cases |
| R-09 | Extract business_purpose using the schema type and allowed values. | snapshot.schema.json: “"business_purpose"” | test_all_source_cases |
| R-10 | Extract start_date using the schema type and allowed values. | snapshot.schema.json: “"start_date"” | test_all_source_cases |
| R-11 | Extract end_date using the schema type and allowed values. | snapshot.schema.json: “"end_date"” | test_all_source_cases |
| R-12 | Extract manager using the schema type and allowed values. | snapshot.schema.json: “"manager"” | test_all_source_cases |
| R-13 | Extract supporting_quotes using the schema type and allowed values. | snapshot.schema.json: “"supporting_quotes"” | test_all_source_cases |
| R-14 | Extract issues using the schema type and allowed values. | snapshot.schema.json: “"issues"” | test_all_source_cases |
| R-15 | Reject extra keys and missing schema properties. | snapshot.schema.json: “"additionalProperties": false” | test_invalid_outputs |
| R-16 | Hash original export bytes with SHA-256 and use the filename as document_id. | materials/office-policy.md: “Use the original JSON file bytes for the source hash and its filename for document_id.” | test_bytes_identity |
| R-17 | Derive business facts only from message, not metadata. | materials/office-policy.md: “Derive request facts from `message`” | test_metadata_is_not_source |
| R-18 | Require supporting quotes to be exact decoded-message substrings. | materials/office-policy.md: “Exact supporting quotes refer to substrings of the decoded `message` value.” | test_invalid_outputs |
| R-19 | Keep absent or unresolved scalar values null and identify them in issues. | materials/office-policy.md: “Represent absent or unresolved scalar values as null and explain each missing or conflicting fact in issues.” | test_missing_dates |
| R-20 | Preserve uncorrected conflicts as null and alternatives as exact quotes. | materials/office-policy.md: “Preserve conflicting alternatives in exact supporting_quotes.” | test_conflicts |
| R-21 | Let explicit corrections replace previous values. | materials/office-policy.md: “A later statement explicitly labelled as a correction replaces the earlier value” | test_corrections |
| R-22 | Leave relative dates unresolved. | materials/office-policy.md: “A relative date stays unresolved.” | test_relative_dates |
| R-23 | For a change extract the requested new permission. | materials/office-policy.md: “For a change request, extract the requested new permission.” | test_changes |
| R-24 | Keep stated request ID separate from document filename and issue mismatches. | materials/office-policy.md: “retain the stated identifier and record the mismatch as an issue.” | test_identifier |
| R-25 | Apply override rule first: review / IT Service Desk / inspect-message. | materials/office-policy.md: “An instruction-override attempt goes to IT Service Desk with status review and next_action inspect-message.” | test_override |
| R-26 | Route dated identified withdrawals to confirmation even with other missing facts. | materials/office-policy.md: “A withdrawal with request_id and request_date goes to IT Service Desk with status review and next_action confirm-withdrawal.” | test_withdrawal |
| R-27 | Route other/null kind, conflicts, mismatches or missing required facts to clarification. | materials/office-policy.md: “Other messages with kind other/null, conflicting details, an identifier mismatch, or any missing required fact go to IT Service Desk with status needs-information and next_action clarify.” | test_clarification |
| R-28 | Clarify inverted date windows without swapping source values. | materials/office-policy.md: “A start_date after end_date is also a clarification issue.” | test_inverted_dates |
| R-29 | Route complete production/write/admin requests to security review. | materials/office-policy.md: “Complete new/change requests involving production, write or admin go to Security Review with status review and next_action review-risk-then-owner.” | test_security |
| R-30 | Route complete staging/read requests to the system owner. | materials/office-policy.md: “Complete staging/read requests go to System Owner with status review and next_action review-request.” | test_complete |
| R-31 | Never output automatic approvals or treat manager naming as approval. | materials/office-policy.md: “All successful intake outputs await human review.” | test_all_source_cases |
| R-32 | Expose extraction failures as null extraction with actionable retry routing. | materials/office-policy.md: “An extraction failure produces status error, owner IT Service Desk, next_action retry-extraction, a null extraction and an actionable error.” | test_provider_failure |
| R-33 | Preserve prior success in history when latest attempt fails. | materials/office-policy.md: “Preserve the last valid result in history when a later attempt fails, and show the latest attempt's error in the current queue.” | test_failed_retry |
| R-34 | Keep one current entry per document on unchanged reruns. | materials/office-policy.md: “An unchanged rerun produces one current queue entry per document.” | test_unchanged |
| R-35 | Retain earlier source versions separately when bytes change. | materials/office-policy.md: “Changed input creates a new result and retains the earlier result with its earlier hash.” | test_changed_source |
| R-36 | Keep credentials in environment and redact operational logs. | materials/office-policy.md: “Keep credentials in environment variables and use credential-redacted operational logs.” | test_provider_contract |
| R-37 | Use a language model through an implemented configurable live adapter. | docs/requirements.md: “Use a language model to extract the request details” | test_provider_contract |
| R-38 | Check response completion before using any extracted data. | docs/requirements.md: “Validate response structure and completion status before using extracted data.” | test_invalid_outputs |
| R-39 | Refresh results when relevant model, schema, prompt or policy settings change. | docs/requirements.md: “refresh affected results when those inputs or settings change” | test_settings_refresh |
| R-40 | Permit operators to inspect completed work while slow work remains pending. | docs/requirements.md: “They want to start on requests that are ready while the rest of the intake is still being prepared.” | test_fast_before_slow |
| R-41 | Maintain coherent shared current records under overlapping operators. | docs/requirements.md: “two operators may start processing around the same time.” | test_concurrent_claims |
| R-42 | Resume unfinished work after an interrupted process. | docs/requirements.md: “continue from the recorded state.” | test_recovery |
| R-43 | Make current queue and extraction source versions agree. | docs/requirements.md: “queue and the supporting extraction records agreeing about the same source version.” | test_export |
| R-44 | Retain earlier documents when absent from later intake batches. | docs/requirements.md: “absence from a later batch does not withdraw an earlier request.” | test_incremental_batches |
| R-45 | Handle malformed responses, provider errors, refusal and interruption explicitly. | docs/requirements.md: “Handle malformed output, provider errors, refusal and interrupted responses explicitly.” | test_invalid_outputs |
| R-46 | Use mocks and require no key or network in automated tests. | docs/requirements.md: “Include automated tests covering a complete request” | test_mock_provider |
| R-47 | Document workload, shared-operation and interruption assumptions and verification limits. | docs/requirements.md: “Record assumptions about workload and shared operation” | test_docs |
| R-48 | Include automated verification for a complete request. | docs/requirements.md: “a complete request” | test_complete |
| R-49 | Include automated verification for missing dates. | docs/requirements.md: “missing dates” | test_missing_dates |
| R-50 | Include automated verification for conflicting details. | docs/requirements.md: “conflicting details” | test_conflicts |
| R-51 | Include automated verification for embedded instructions. | docs/requirements.md: “embedded instructions” | test_override |
| R-52 | Include automated verification for provider failure. | docs/requirements.md: “provider failure” | test_provider_failure |
| R-53 | Include automated verification for an unchanged rerun. | docs/requirements.md: “an unchanged rerun” | test_unchanged |
| R-54 | Include automated verification for changed source content. | docs/requirements.md: “changed source content” | test_changed_source |
| R-55 | Include automated verification for a paraphrased synthetic request. | docs/requirements.md: “a paraphrased synthetic request” | test_synthetic |
| R-56 | Include automated verification for refusal or interrupted responses. | docs/requirements.md: “refusal or interrupted responses” | test_invalid_outputs |
| R-57 | Include automated verification for a failed retry after a prior success. | docs/requirements.md: “a failed retry after a prior success” | test_failed_retry |
| R-58 | Write setup/runtime/provider/environment/intake/test/accuracy/queue instructions in README.md. | CHALLENGE.md: “Setup, supported runtime/provider, exact intake/test/accuracy-check commands” | test_docs |
| R-59 | Supply runnable source, extraction prompt, schema, request configuration and dependency lockfile. | CHALLENGE.md: “Source code and dependency lockfile” | test_docs |
| R-60 | Export one extraction record with all required envelope fields per current message. | CHALLENGE.md: “One current record per message: document_id, source_sha256, extraction” | test_export |
| R-61 | Export a queue linked by document_id to extraction records. | CHALLENGE.md: “The review queue linked to extraction records by document_id” | test_export |
| R-62 | Write source-derived accuracy expectations for all 20 supplied messages plus one paraphrase. | CHALLENGE.md: “Source-derived expected fields for the 20 supplied messages and one paraphrase you author” | test_accuracy |
| R-63 | Describe exact-match counts, denominator, factual errors, configuration and mock/live provenance. | CHALLENGE.md: “exact-match counting/denominator rules, factual-error reporting and model/configuration” | test_accuracy |
| R-64 | Provide credential-redacted example request and implemented response handling. | CHALLENGE.md: “Credential-redacted example model request showing the model ID and configuration used, plus the implemented response handling” | test_provider_contract |
| R-65 | Write verification commands, comparisons, limits and observed results in verification.md. | CHALLENGE.md: “Verification commands and assertions, their intended comparisons, operating limits” | test_docs |
| R-66 | Pair coding-session capture with submitted commit. | CHALLENGE.md: “Session record paired with the submitted commit” | manual_capture |
| R-67 | Commit and push to default branch and submit root repository URL. | CHALLENGE.md: “Commit and push the application, outputs and session capture to your repository's default branch.” | manual_submission |

## Open questions

- Capture: `python3 tools/check_prerequisites.py` reports Entire is missing. Obtain the facilitator's capture setup; no retrospective session capture is claimed.
- Accuracy: the brief does not specify a canonical business-purpose string or semantic metric. This implementation uses frozen verbatim purpose spans with literal comparison; equivalent paraphrases count as exact-match differences. Report differences rather than asserting factual errors automatically. The optional user preference remains unanswered.
- Instruction attempts have no exhaustive definition. Use the model's issues plus a conservative deterministic detector for known override phrases; report that unseen attacks need human review. Preserve the original request permission in IT-006, with the attempted admin instruction retained only as evidence.
- Shared topology and rate allocation are unspecified. Choose one host with local SQLite, multiple processes and bounded per-process concurrency/rate. Multi-host/network-filesystem deployment is outside the verified scope.
- No total ordering of exported_at is specified. Use intake transaction order for competing different revisions, not metadata timestamps.
- Exact output wording for issues is unspecified; tests assert issue categories/presence, source facts, and routing rather than treating issue prose as business truth.
- Real model availability is account-dependent. Use configurable OpenAI Responses API model `gpt-4.1-mini` as the documented example; no live availability or accuracy claim is made.
