# Northstar IT access-request intake

A CLI turns exported messages into structured facts and a human review queue. It uses the supplied office policy, exact source evidence, independent workers, and a durable SQLite attempt ledger. It never grants access.

## Setup and quick start

Run from the repository root with **Python 3.10 or later on Linux/macOS**. There are no third-party packages to install: `requirements.lock` locks an empty dependency set. Python 3.12.3 is the runtime tested in this session.

```bash
python3 --version
python3 -m access_intake --help
# Offline demo: no API key, no model/network calls.
env -u API_KEY python3 -m access_intake intake materials/requests
python3 -m access_intake queue
python3 -m access_intake queue --json
python3 -m access_intake history IT-001.json
python3 -m access_intake export --out deliverables
```

Default state is `.state/intake.db`, which is ignored by Git. Default provider is `mock`. The 20 demo replies and a fresh paraphrase are saved under `tests/mock_responses/`. These are manually authored examples, not measured model performance. Mock mode rejects unknown documents or changed message content rather than pretending to extract fresh wording. Changes only to export metadata/JSON whitespace can reuse a matching message fixture while still producing a new source version.

`document_id` is the filename. Two different paths with the same basename identify the same document; keep basenames unique unless intentionally replacing a document. The ID written inside the message remains a separate field. A differing filename stem adds an identifier-mismatch issue for every document name, including names outside the supplied IT examples. Policy precedence still applies: override attempts and eligible withdrawals route before clarification.

## Intake, handover and recovery

Global options go **before** the subcommand. You can pass files or directories; each directory contributes its top-level `*.json` files.

```bash
# Enqueue durably, then start work. Use a separate terminal for queue inspection.
python3 -m access_intake --db .state/team.db intake materials/requests --enqueue-only
python3 -m access_intake --db .state/team.db --workers 4 resume
python3 -m access_intake --db .state/team.db queue
python3 -m access_intake --db .state/team.db queue --json

# See earlier attempts and source hashes.
python3 -m access_intake --db .state/team.db history IT-010.json

# Explicitly retry with the attempt's saved provider/settings and bytes.
python3 -m access_intake --db .state/team.db retry IT-010.json
python3 -m access_intake --db .state/team.db resume

# A repeat intake skips identical source/settings, including an existing error.
python3 -m access_intake --db .state/team.db intake materials/requests
# Force a new attempt, retaining prior attempts.
python3 -m access_intake --db .state/team.db intake materials/requests/IT-001.json --force
```

Completed records remain visible while other messages are running. Current records may have state/status `pending` or `running`; those are unfinished work, not business review decisions. Completed successful extraction is routed to `review` or `needs-information`; failures have status `error`, null extraction, an actionable message, and `retry-extraction`. The latest attempt is always current, even if it fails; earlier success is available only in history. Enqueuing a replacement immediately exposes its pending state so an older success is not presented as the new result.

After a process is killed, pending work can resume immediately. Running work becomes reclaimable when its lease expires; `queue --json` shows `lease_until` as Unix seconds. Leases are conservatively sized from saved timeouts/retry settings (default 240 seconds) and extended while the worker is active. Run `resume` again after expiration if no eligible work was available on the first run. A fencing token prevents a reclaimed attempt's older worker from publishing a result. SIGTERM/host outage recovery is at-least-once model calling: a remote request may have completed before local persistence. No external access-grant side effect exists. Ctrl-C stops taking new work and allows active bounded calls to settle before exit.

An unchanged source/settings combination reuses the latest attempt; changes to original bytes, model, prompt, schema, policy, provider or response configuration create a new attempt. Resume/retry use immutable saved settings. To switch provider/model/settings, use a fresh `intake` command with the new options. Input absence in a later batch never withdraws a document. A withdrawal must be stated in its message. Malformed UTF-8/JSON or missing message text becomes an error for that document without blocking others.

## Live provider

The implemented integration sends HTTPS requests to the OpenAI Responses API. A supported example configuration is `gpt-4.1-mini` with strict JSON Schema output and `max_output_tokens=3000`. Model access depends on the supplied account; this session did not call a live model. Set the facilitator-supplied **`API_KEY`** in your environment. It is the only application environment variable and is read only in live mode. Do not put it in source files or command arguments.

```bash
# Set API_KEY securely in your terminal/environment first.
python3 -m access_intake --provider openai --model gpt-4.1-mini --workers 4 --timeout 30 --retries 2 --interval 1 --max-output-tokens 3000 intake materials/requests
python3 -m access_intake queue
python3 -m access_intake export --out deliverables
```

The extraction prompt is `access_intake/prompt.txt`; the trusted policy is `materials/office-policy.md`; the output schema is `snapshot.schema.json`. Source message text is sent as user data, separated from trusted instructions. Provider response completion and message completion, refusal, JSON shape/types/enums, dates and quote substrings are checked before routing. Uncertainty remains null with issues. Source-derived fixture tests exercise explicit corrections, conflicts, relative dates, ID mismatches and requested new permissions. Schema validity alone cannot establish semantic accuracy; use the source comparison procedure.

Retries are bounded (0–5 retries): 429, 5xx, timeouts and connection errors retry with exponential delay; numeric Retry-After is capped at 30 seconds. Permanent HTTP errors, malformed JSON, refusal and incomplete extraction become explicit errors; retry them after inspection. Error handling does not print provider bodies, headers, credentials or raw unexpected exception details. The application does not log HTTP payloads. Request evidence is credential-redacted.

The current policy router implements the supplied five rules in order; detected instruction attempts always go to the Service Desk, then eligible withdrawals, clarification, security review, and staging/read owner review. The model's issue flags and a deterministic detector recognize known override phrases. Unseen prompt-injection patterns are not exhaustively detected. A policy revision that changes routing rules requires updating `route()` and its source-derived tests as well as the policy document; re-intake then refreshes results. No automatic approval state exists.

API contract sources: [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses) and [Responses API reference](https://developers.openai.com/api/reference/resources/responses/methods/create).

## Export and accuracy checks

```bash
python3 -m access_intake export --out deliverables
# Run the independent paraphrase in a separate database to keep the main export at 20 records.
env -u API_KEY python3 -m access_intake --db .state/synthetic.db intake examples/requests
python3 -m access_intake --db .state/synthetic.db export --out deliverables/synthetic
# Compare the two exports to frozen source expectations, never to previous program output.
python3 -m access_intake accuracy --records deliverables/extractions.jsonl deliverables/synthetic/extractions.jsonl --out deliverables/accuracy.md
python3 -m access_intake request-evidence --out deliverables/request-evidence.json
```

`extractions.jsonl` has one current record per document, including source hash, processing key, policy hash, attempt ID, extraction/null, routing, error, and response_source (`mock` or `openai/<model>`). Its `configuration` contains timeout, retries, interval, output-token limit and prompt/schema hashes. The accuracy report lists these settings with each source hash, configuration key, configured model and producing response source. Provider labels alone cannot distinguish a live call from fake HTTP; observations must say which transport was used. `queue.json` links to the same attempt and source version. `history.jsonl` retains prior attempts separately. The database also retains original source bytes, saved configuration and enqueue/claim/completion events.

Each export reads one database transaction and writes an immutable generation under `snapshots/`. `snapshot.json` names that generation and its file checksums. Concurrent writers use a filesystem lock. For a consistent pair during concurrent export, read `snapshot.json` once and read both files under its `generation` directory; verify its checksums. Top-level files are convenient copies for static submission and individually replaced atomically; they are not a multi-file transaction. Live operational reads use the transactional `queue` command.

Accuracy compares 12 scalar fields per document (252 comparisons across 21 documents), with exact string/null equality, and 63 independent routing comparisons. Missing/error results count as mismatches, including expected nulls. Business-purpose values use frozen verbatim source spans; equivalent wording can differ under this metric and is not automatically a factual error. Supporting quote and issue wording is assessed separately. `deliverables/accuracy.md` provides the procedure, expected fields, observed configuration/provenance and differences. A perfect mock comparison checks the pipeline against authored fixtures; it does not establish model extraction accuracy.

## Tests and verification

```bash
env -u API_KEY python3 -m unittest discover -s tests -v
# Save stdout and stderr as an auditable result:
env -u API_KEY python3 -m unittest discover -s tests -v > planning/test-run.txt 2>&1
python3 tools/check_prerequisites.py
```

The completed full run passed **56 tests in 50.012 seconds on Python 3.12.3**; [planning/test-run.txt](planning/test-run.txt) contains its stdout/stderr. All tests use saved replies or fake HTTP, with network access blocked in integration tests and their child interpreters. No real API key is read or required; credential tests patch the lookup to a test sentinel. No live model is invoked. Tests cover all 20 messages and the paraphrase, failure after prior success, concurrency in two processes, stale-worker fencing, partial visibility, revision/settings refresh, strict validation, API payload and retries, coherent exports, and CLI commands. The initial missing-module failure is in `planning/test-first.txt`; it is a combined pre-implementation baseline, not a separate red/green commit for each build step.

`planning/spec.md`, `planning/plan.md` and `planning/validation.md` trace requirements to implementation evidence. `deliverables/verification.md` records observed results and limits. The current prerequisite check reports Entire enabled for Codex. CLI availability and enabled status alone do not prove that the facilitator's required session artifact matches the submitted commit. Capture-artifact review, commit pairing, remote push and Classroom receipt remain separate submission checks. Historical test/implementation commits are described in validation; no retrospective test-first or capture history is claimed.

## Operating scope

The design targets the stated 200–400 daily messages and a 2,000-message burst with a bounded worker pool (default 4, maximum 32). A measured 2,000-message offline smoke run is documented in verification; it is not a live throughput guarantee. All regional operators must access the **same local SQLite file on one host**. SQLite WAL and short immediate transactions serialize intake/claims while readers continue. Do not put the database on a network filesystem or copy it independently across offices. Multi-host distribution is outside this implementation's scope.

Intake transaction order defines the latest revision when operators submit different content for one filename; export timestamps do not order source truth. Rates are bounded **per process**; coordinate a total budget across operators because the shared provider quota may include other applications. Leases prevent duplicate active local claims, but interruption may lead to repeated remote calls. Histories and immutable export generations grow without pruning; plan backups and retention for long-term operation. Back up SQLite using its backup API, or with all workers stopped; copying only the main database while WAL is active is unsafe.

The CLI assumes a trusted local operator; it has no authentication, role management, central server or automatic access provisioning. Human reviewers make all decisions. Submission still requires facilitator-compatible session capture, a commit/push to your fork's default branch, and the root repository URL in Classroom as described in CHALLENGE.md.

## Submission readiness

[planning/validation.md](planning/validation.md) reviews every deliverable in [CHALLENGE.md](CHALLENGE.md) and all 146 current requirements. The application, empty dependency lockfile, prompt/schema, 20 supplied mock records, linked queue, separate authored paraphrase, accuracy report, redacted request evidence and verification document are ready locally. The mock comparison matches 252/252 scalar fields and 63/63 routing fields; a live model call or real API key is unnecessary for this submission.

Submission remains pending until the facilitator-compatible session capture is inspected and paired with the final commit, the application/outputs/capture are committed and pushed to the default branch (`main`), and the Classroom receipt is verified. Submit only the root repository link: `https://github.com/gitpadma-2026/ai-full-stack-it-access-requests`. The commit containing this document packages the completed local changes; remote push and capture pairing still require verification.
