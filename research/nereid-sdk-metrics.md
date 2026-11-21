# Nereid SDK controller metrics: assessment and proposal

Asked by the owner (2026-11-17), from a voice session. Assessment and proposal only; nothing implemented.

## Summary

- **The SDK exists and is custom:** `lib/nereid` (`nereid-sdk` 0.2.0, #754), no Kopf, no work queue. Each Nereid runs one thread with a periodic, level-triggered pass over everything it owns (`passes.forever` + `passes.Pace`).
- **Metrics already exist, under Nereus names:** six `nereus_nereid_*` series on every Nereid's `GET /metrics`, through OpenTelemetry's Prometheus exporter. 19 Nereids pin `nereid-sdk==0.2.0`; all 21 with a loop use `telemetry`/`passes`.
- **Scraping already works:** the `victoriametrics` Nereid's `VMPodScrape nereids` picks every pod labelled `core.<domain>/metrics: "true"` in `nereus-system`, which the CLI sets on every Nereid it deploys. A new Nereid is discovered with zero effort.
- **The gap is the names:** none of the controller-runtime / client-go workqueue names exist, so community dashboards do not work. Several workqueue metrics have no honest meaning in a queue-less, one-worker loop and must be mapped with care.
- **The portal view is already designed:** #744 (each Nereid's golden signals, with sparklines on the phone), on top of #740 (home screen, one row per reef and Nereid) and #746 (baselines). No reef has an icon today.

## Decisions (owner, 2026-11-17)

- **SDK design accepted:** `nereid-sdk` 0.3.0 emits the controller-runtime and workqueue names alongside `nereus_nereid_*`, both kept.
- **#744 is adjusted,** not replaced: its queries move to the standard names.
- **Reef icon:** an `icon` field on the Nereid's `GET /` contract (an amendment to ADR 0022), naming an icon of an open-source set vendored in the portal, `honeycomb.svg` when missing.
- **Dashboards:** only the portal for now; a Grafana Nereid in the metrics reef stays an idea for later.

## 1. The SDK

Location: `lib/nereid/src/nereid/` — `telemetry.py`, `passes.py`, `logs.py`, `screens.py`, `addresses.py`.

| Question | Finding |
| --- | --- |
| Framework | None. Plain Python, `threading`, `urllib` against the Kubernetes API (each Nereid has its own `kube.py`). Kopf is not used anywhere. |
| Reconciliation | A *pass*: one call that reconciles the Nereid's whole world (all its objects), level-triggered, no watches (no `?watch=` anywhere in `controllers/`). |
| Work queue | None. No per-object keys, no dedup, no rate limiter. |
| Retries | Implicit: a failed pass sets `Ready=False` with a reason and the next lap runs again. `passes.publish` retries a failed status write on the next lap. `passes.forever` never dies (#932). |
| Concurrency | One reconcile thread per Nereid (17× `threading.Thread(target=loop, …)`), so max concurrency is 1. The HTTP server runs in a separate daemon thread. |
| Pace | `passes.Pace` (#1297): `idle` seconds between laps, `busy` (1 s) for 30 s after a pass reported work. |
| Existing metrics | `telemetry.py`, OpenTelemetry SDK + `PrometheusMetricReader` on a private `CollectorRegistry`, text format 0.0.4. No `process_*` collector. |

The six metrics today (`lib/nereid/README.md`, pinned by `tests/test_telemetry.py`):

| Metric | Type | Labels |
| --- | --- | --- |
| `nereus_nereid_reconcile_total` | counter | `nereid` |
| `nereus_nereid_reconcile_errors_total` | counter | `nereid`, `reason` |
| `nereus_nereid_reconcile_duration_seconds` | histogram, 5 ms – 60 s | `nereid` |
| `nereus_nereid_reconcile_period_seconds` | gauge | `nereid` |
| `nereus_nereid_last_success_timestamp_seconds` | gauge | `nereid` |
| `nereus_nereid_ready` | gauge 1/0 | `nereid`, `reason` |

## 2. The metrics reef and the VictoriaMetrics Nereid

`controllers/victoriametrics/` (reef `metrics`), objects in `nereus-system`:

- VMSingle `nereus` (14 d retention), VMAgent `nereus` with `selectAllByDefault: false` (only its own scrape objects).
- **VMPodScrape `nereids`:** selector `core.<domain>/metrics: "true"`, namespace `nereus-system` only, port `http`, path `/metrics`, label `nereid` from the pod's `app.kubernetes.io/name`, `honorLabels: false` (a series cannot fake its `nereid`). Built in `cli/src/nereus/local_nereids.py:426`; the label is put on every Nereid pod in `cli/src/nereus/cluster.py:2683` (`METRICS_LABEL`).
- VMNodeScrape `kubelet-cadvisor` for CPU and memory per container.
- ADR 0025 (metrics enter from outside only through the Nereus API, with declared sources) reserves the `nereus_` prefix and the `nereid` label for the platform; scraped Nereid metrics are unaffected.

**Discovery of a new Nereid:** automatic. Deployed by `nereus nereid apply` → labelled → scraped. Nothing for the author to do.

## 3. Open source first

- **controller-runtime** (kubebuilder metrics reference, checked 2026-11-17) defines: `controller_runtime_reconcile_total`, `controller_runtime_reconcile_errors_total`, `controller_runtime_terminal_reconcile_errors_total`, `controller_runtime_reconcile_time_seconds`, `controller_runtime_max_concurrent_reconciles`, `controller_runtime_active_workers`, the webhook metrics, `rest_client_requests_total`, and the client-go workqueue set (`workqueue_depth`, `workqueue_adds_total`, `workqueue_queue_duration_seconds`, `workqueue_work_duration_seconds`, `workqueue_unfinished_work_seconds`, `workqueue_longest_running_processor_seconds`, `workqueue_retries_total`). Labels (from controller-runtime's source, not the reference page, which lists none): `controller` on all `controller_runtime_*`, plus `result` (`success`, `error`, `requeue`, `requeue_after`) on `reconcile_total`; `name` (and `controller` in recent versions) on `workqueue_*`. To pin against the vendored version before implementing.
- **Kopf:** exposes only a liveness/health endpoint; no Prometheus metrics (docs.kopf.dev, "Health-checks"). Adopting Kopf would bring watches and per-object handlers but not the metrics, and would mean rewriting 21 Nereids: out of scope.
- **No Python library** found that emits the controller-runtime names. `prometheus_client` (already a dependency) is the right building block; the SDK already owns the registry.

Conclusion: adopt the *names and labels* (the standard), build the thin emitter in the SDK, where it already is.

## 4. Proposed metrics layer in the SDK

### Principles

- **Zero effort:** emitted from `telemetry.reconcile_pass()` and `passes.forever`/`Pace`, which every Nereid already calls. Bump `nereid-sdk` to 0.3.0, bump the pin in the 19 `requirements.txt`; no Nereid code changes.
- **Deterministic:** pure counters/gauges from the loop; no AI anywhere.
- **Honest:** a metric with no meaning in this model is emitted with its truthful constant value (or not at all), never faked to look like a busy queue.
- **`controller` label = the Nereid's name** (the value of `setup(nereid=…)`); the scrape still adds `nereid`.

### Mapping

| Standard metric | Meaning in a Nereid | Source in the SDK |
| --- | --- | --- |
| `controller_runtime_reconcile_total{controller,result}` | one per pass; `result="error"` on failure, `"requeue"` when the pass called `Pace.busy()`, else `"success"` | `reconcile_pass()` |
| `controller_runtime_reconcile_errors_total{controller}` | failed passes | `reconcile_pass()` (keeps the Nereus `reason` only on `nereus_nereid_reconcile_errors_total`) |
| `controller_runtime_terminal_reconcile_errors_total{controller}` | passes failing with one of `known` (a refusal the Nereid raises on purpose) | `passes.run` |
| `controller_runtime_reconcile_time_seconds{controller}` | pass duration | same histogram data, controller-runtime buckets |
| `controller_runtime_max_concurrent_reconciles{controller}` | constant 1 | `setup()` |
| `controller_runtime_active_workers{controller}` | 1 while a pass runs, else 0 | `reconcile_pass()` |
| `workqueue_depth{name,controller}` | 1 when a lap is due and not started, else 0 (practically 0) | `forever` |
| `workqueue_adds_total{name,controller}` | laps scheduled | `forever` |
| `workqueue_queue_duration_seconds{name,controller}` | lateness of a lap: actual start minus scheduled start | `forever` |
| `workqueue_work_duration_seconds{name,controller}` | pass duration | `reconcile_pass()` |
| `workqueue_unfinished_work_seconds{name,controller}` | seconds the current pass has been running | callback gauge |
| `workqueue_longest_running_processor_seconds{name,controller}` | same as above (one worker) — the most useful one: a stuck pass shows up | callback gauge |
| `workqueue_retries_total{name,controller}` | passes started right after a failed pass | `forever` |
| `process_*` (CPU, RSS, fds, start time) | `prometheus_client.ProcessCollector` on the SDK registry | `setup()`; used by the community dashboards |
| `rest_client_requests_total{code,method,host}` | optional, later: needs a hook in each Nereid's `kube.py`; candidate for moving `Kube` into the SDK | out of this step |

### Migration of the Nereus names

The `nereus_nereid_*` set stays (it carries what the standard lacks: `reason`, `period`, `last_success`, `ready`). Emit both sets in 0.3.0. Then either keep both (cardinality is tiny: ~20 Nereids × ~15 series) or drop the two duplicated ones (`reconcile_total`, `reconcile_duration_seconds`) after #744's queries move to the standard names. Recommendation: keep both; drop nothing until the portal is on the standard names.

Rejected alternative: VMRule recording rules that rename `nereus_*` to `controller_runtime_*` in the store. Deterministic and no SDK change, but cannot produce `active_workers`, `unfinished_work_seconds` or `process_*`, and dashboards querying a raw `/metrics` would not see them.

### Dashboards

The Kubebuilder Grafana plugin (`grafana/v1-alpha`) generates `controller-runtime-metrics.json` and `controller-resources-metrics.json` that query these names (and `process_*`, `job`). Nereus ships no Grafana; VictoriaMetrics' vmui can import Grafana-style queries but not the dashboards. Worth a follow-up decision: a Grafana Nereid in the metrics reef, or only the portal view below.

## 5. Portal view (RED per Nereid)

Already specified by **#744** (each Nereid's golden signals from the metrics reef, with sparklines on the phone), on the rows of **#740** (portal home screen, one row per reef and Nereid) and **#746** (baseline thresholds, then 7-day baselines). #744 defines `signals` on each `GET /v1/status` row: `rate`, `errorRatio`, `p95Seconds`, `saturation`, CPU and memory, with 1 h series for sparklines, one query per signal for all Nereids (`by (nereid)`).

Proposed adjustments to #744, not a new issue:

- **R**ate: `sum by (nereid) (rate(controller_runtime_reconcile_total[5m]))`.
- **E**rrors: `sum by (nereid) (rate(controller_runtime_reconcile_errors_total[5m])) / R`.
- **D**uration: `histogram_quantile(0.95, sum by (nereid, le) (rate(controller_runtime_reconcile_time_seconds_bucket[5m])))`.
- Keep saturation (mean pass time over period) and add `workqueue_longest_running_processor_seconds` as the "stuck" flag.
- Layout: one compact row per Nereid (icon, name, state chip, R · E% · p95, one sparkline) on the phone; a table with all sparklines on desktop.

**Reef icons:** no reef has one. Only ADR 0022 screens carry an `icon` name (validated by `/^[a-z0-9-]{1,40}$/` in `static/screens.js`, used today only by `leagore`), and the portal only sets it as `data-icon` with no icon set behind it. Proposal: an `icon` field on the Nereid's `GET /` contract (ADR 0022's `contractVersion: 1` allows new fields), merged into its status like the screens, from one shared, open-source icon set vendored in the portal (e.g. Lucide, ISC); fallback `honeycomb.svg`.

## Gaps

1. No controller-runtime / workqueue names or labels: community dashboards do not work.
2. No `active_workers` / in-flight gauge: a stuck pass is invisible until `last_success` ages.
3. No `process_*` metrics on the SDK registry (CPU/memory come only from cAdvisor).
4. No `result` dimension (requeue vs success).
5. No API client metrics (`rest_client_requests_total`): each Nereid has its own `kube.py`.
6. #744's queries use the Nereus names; no portal signals implemented yet.
7. No reef icon anywhere; no icon set in the portal.

## Next steps

1. Pin the exact labels from the controller-runtime version to follow (source, not the reference page), and write the mapping table into `lib/nereid/README.md` as the contract.
2. `nereid-sdk` 0.3.0: emit the standard set alongside `nereus_nereid_*`, `ProcessCollector`, tests in `tests/test_telemetry.py` pinning the exposition; bump the 19 pins.
3. Check `make scene-metrics` (`test/scene-metrics`) sees the new series through the VMPodScrape.
4. Update #744's queries to the standard names; then deliver #739/#740/#744.
5. ADR 0022 amendment: the reef `icon` field and the portal's icon set (decided).
6. Later: move `Kube` into the SDK and add `rest_client_requests_total`; a Grafana Nereid only if the portal falls short.
