# 0013. The Nereids' screens in the portal: the home in a list or a grid, and each Nereid live

**Status:** Proposed (2026-11-23)

From the owner's session of 2026-11-23, part of journey #1816 (the Nereids' metrics: the standard controller names in the SDK, RED on the phone, ECharts on the desktop). The owner shaped it on a clickable prototype on the phone, kept next to this file: [`0013-nereids-screens/prototype.html`](0013-nereids-screens/prototype.html) (invented data, simulated live updates). Raw data in the session's Pontos log; the idea of one metrics layer in the SDK comes from the voice session `#pontos/raw/2026-11-17/1731-voice-nereid-sdk-controller-metrics.md`.

## Intent

The portal's home (#740, the status: one row per reef and Nereid) answers "is anything out of the expected?" well, but each row says little next to what the platform knows. The owner wants:

- the home to show more Nereids at once, and more about each, without losing the "problems first" reading;
- a tap on a Nereid to open its own screen, with its metrics live, to understand how it is doing now.

The screens follow Material Design 3, as the portal does since #1838.

## Decisions (owner, 2026-11-23)

- **Both home views, with a toggle.** The list and the grid each show the Nereids in their own way; the owner keeps both. The switch is an icon-only M3 segmented button (list | grid), on the row of the filter chips, at its right end; the choice is kept in the browser.
- **The filter chips** (All, Attention, Ready) apply to both views. They carry no counts: the summary card already says them, and the row fits 340 px only without them.
- **The detail screen** shows the four RED signals live, and the Nereid's pods: CPU and memory over time, pods ready over desired, restarts, requests and limits, the last restart's reason, and each pod.
- **Pod data comes from the observability side, never from the Nereus API reading pods.** In the owner's words, reading pods would make the API do what belongs to observability. A second opinion (Fable) agreed: in Nereus the object is the Nereid (ADR 0002), the pod is an operation detail.
- **kube-state-metrics enters the metrics reef, in a later slice,** limited to pods and deployments (no Secrets). Approved by the owner, after the cAdvisor slice.
- **Out:** the domain events and the audit trail of the "observable and auditable Nereids" idea (`#pontos/raw/2026-11-19/0236-voice-idea-journey-observable-auditable-nereids.md`); no journey covers it yet, and it is not this one.

## Approaches considered

**Home layout.**

- *List* (today's rows plus a RED line and a sparkline): keeps the reading of today, about 7 Nereids on a phone screen, the reason of a problem in the row.
- *Grid* (two columns of M3 cards, one big number and a sparkline each, the attention cards outlined in their colour): about 12 Nereids on screen, the reason left to the detail.
- *Both, with a toggle*: chosen by the owner; each answers a different glance.

**Where the pods' data comes from.**

- *A. The Nereus API reads the pods from the Kubernetes API:* no new component, current values only; gives the API new pod-read RBAC (a pod's spec exposes `env`) and a Nereid-to-pod mapping, and `lastState` vanishes when a pod is replaced. Refused by the owner.
- *B. kube-state-metrics in the metrics reef, everything through MetricsQL:* one more component and a ClusterRole, history for the restart counter, the community's dashboards; the last terminated reason is only a gauge that also vanishes with its pod.
- *C. cAdvisor first, then a minimal kube-state-metrics:* chosen. VictoriaMetrics already scrapes each kubelet's `/metrics/cadvisor` (`kubelet-cadvisor` in `controllers/victoriametrics/victoriametrics.py`), which already gives CPU, memory, the limits (`container_spec_memory_limit_bytes`, `container_spec_cpu_quota`), restarts with history (`changes(container_start_time_seconds)`) and OOM kills (`container_oom_events_total`). kube-state-metrics adds only the requests, ready over desired and the non-OOM restart reasons.

## The screens

The prototype is the reference for the look; the words below are the rules.

### Home

```text
┌ Nereus                                   ┐
│ nereus · portal.getnereus.dev            │
│ ┌──────────────────────────────────────┐ │
│ │ ● 2 need attention              ⟳   │ │
│ │   20 reefs · 19 Nereids · 20:29      │ │
│ └──────────────────────────────────────┘ │
│ (All)(Attention)(Ready)        [☰|▦]    │  ← filter chips, view toggle
│                                          │
│ List:  ⟳ release · flux        Degraded  │
│          ReconcileFailed: helm upgrade…  │
│          0.31/s  12% err  p95 840ms      │
│          ▁▂▁▃▂▅▃▂▁▂▃▂                     │
│                                          │
│ Grid:  ┌──────────┐ ┌──────────┐         │
│        │⟳        ●│ │◍        ●│         │
│        │release   │ │edge      │         │
│        │flux      │ │envoy-gw  │         │
│        │0.31/s 12%│ │4.8/min 0%│         │
│        │▁▂▁▃▂▅▃▂▁ │ │▁▂▂▁▂▁▂▂▁ │         │
│        └──────────┘ └──────────┘         │
└──────────────────────────────────────────┘
```

- Problems first in both views: the list keeps today's "Needs attention" and "All good" sections; the grid puts the attention cards first, outlined in their state's colour (red Degraded, amber Progressing).
- A rate below 0.1 passes/s reads per minute (`4.8/min`), else per second; the error ratio turns red above zero; p95 in ms below one second.
- The sparkline is the rate of the last hour, coloured by the row's state.
- Without the metrics reef (`signals: null`, #744), the rows keep today's form and one line says "no metrics: install the metrics reef"; the toggle and the chips stay.

### Detail

```text
┌ ←                                    ⋮ ┐
│ ⟳  release                  Degraded   │
│    Nereid flux · 0.1.34                │
│ ┌ ReconcileFailed: helm upgrade timed… ┐│
│ ( 5m | 1h | 24h | 7d )                 │  ← segmented button, the range
│ ┌ Rate ──────┐ ┌ Errors ────┐          │
│ │ 0.26/s ▁▂▃ │ │ 15%    ▁▅▃ │          │
│ ┌ Duration ──┐ ┌ Saturation ┐          │
│ │ 652ms  p95 │ │ 31%   busy │          │
│ Pods · 1/1 ready                       │
│ ┌ CPU 162m ──┐ ┌ Memory 205Mi┐         │
│ CPU    ████░░░░░░░░ ▲request  of limit │
│ Memory ███████████░ ▲request  of limit │
│ Restarts · 24h 3 · Queue depth 3       │
│ nereus-flux-…-qdmup   Ready            │
│   node · 11m · 3 restarts · last OOM   │
│─────────────────────────────────────── │
│ ● Live                    updated 20:29│  ← bottom bar, away from the camera
└────────────────────────────────────────┘
```

- The four RED signals, each a number and a chart of the chosen range: Rate (passes), Errors (% of passes), Duration (p95), Saturation (the share of time the Nereid is busy, as #744 defines it).
- The range is an M3 segmented button: 5m, 1h (default), 24h, 7d.
- Pods: CPU and memory as numbers and charts; a meter of each against its limit, with a mark at the request; restarts in 24h; the queue depth; one line per pod with its node, age, restarts and the last restart's reason.
- While the screen is visible, it refreshes on its own; the "Live" mark and the time of the last update sit in the bottom bar, never at the top centre (`docs/agent/decks.md`, screens on a phone).
- With a value missing (no metrics reef, no kube-state-metrics yet), its card says what is missing in one line instead of a zero.

## The slices

Each slice is one sub-issue of #1816, shipped and shown before the next.

1. **The home's signals, in both views** (#744, adjusted): the `signals` field of each row of `GET /v1/status` (its contract in #744), the list's RED line and sparkline, the grid view, the chips and the toggle. RED from `nereus_nereid_*` today; the queries move to `controller_runtime_*` when #1814 lands.
2. **The detail screen, RED plus cAdvisor** (#2176): a new route of the Nereus API for one Nereid's series over a range, the screen, the pods' CPU, memory, limits, restarts and OOM kills from cAdvisor. Done when, in the scene, a Nereid given a low memory limit is OOM-killed and the screen shows the restart and the OOM.
3. **kube-state-metrics in the metrics reef** (#2177): only `--resources=pods,deployments`, scraped by the VMAgent; the screen gains the requests, ready over desired and the last restart's reason.

The reefs' icons on the rows and cards are #1773's (each reef has its own icon); until then every row keeps the default icon. The desktop's richer charts are #1815's.

## Constraints

- The portal reads the series only through the Nereus API (ADR 0018, the API is the one door; ADR 0025, metrics enter only through it); the browser never reaches VictoriaMetrics.
- One request per signal for all Nereids at once on the home (`by (nereid)`), never one per row (#744).
- The series of a Nereid are told by the `nereid` label the VMPodScrape sets from the pod's `app.kubernetes.io/name` (never from the series itself). cAdvisor's series carry `namespace` and `pod`, not `nereid`: the API joins them on `namespace, pod` with a series of the Nereid's own scrape, once, in a function both slices use.
- Screens on a phone follow `docs/agent/decks.md`: both languages measured at 340, 360, 390 and 412 px, the controls of a row shrink, nothing live at the top centre.
- The `localStorage` read is guarded: a browser that blocks it opens the list view and keeps no choice (the prototype showed a blank page in a sandboxed preview until it was guarded).

## Calls made while writing (the session's, not the owner's)

From the builder check of this file; the owner may overturn any of them.

- **The join holds over the whole range:** a Nereid's pods are replaced (a rollout, an OOM kill), so the join of cAdvisor to the Nereid runs inside the range query (`group_left` on `namespace, pod` against the Nereid's own scrape series over the same range), never as an instant lookup that would drop the older pods. The VMPodScrape keeps `namespace` and `pod` on every series it scrapes.
- **What slice 2 shows per pod with cAdvisor only:** the node from the kubelet's series, the age from `container_start_time_seconds`, restarts from its changes, and as the last reason only `OOMKilled` (from `container_oom_events_total`); any other reason waits for slice 3. The queue depth needs `workqueue_depth`, so its card says what is missing until #1814 lands.
- **A Nereid is named by its reef and its Nereid,** as the rows of `GET /v1/status` are; the detail route takes both. A row with no Nereid (a reef with only kinds) shows in both views with its state and no numbers, and opens no detail.
- **No scoping by person:** the status of the instance's Nereids is the instance's, the same for everyone who may read `GET /v1/status` today; the queries take no tenant label.
- **7d fits:** the VMSingle keeps 14 days.
- **Missing values are per field:** when the metrics Mandate answers but one query fails, only that field is `null` and its card says so; `signals: null` stays for "no metrics reef or it does not answer".

## Not in this design

- A "Reconcile now" action: a write, which needs its own right; its own issue when wanted.
- A link out to vmui: exposing vmui is the owner's decision in #1816's envelope, and #1815's.
- Recent events on the detail screen: they would mean reading Kubernetes Events, the same concern as reading pods; they wait for the domain events idea above.
- Baselines and their colours (#746).

## Left to the builder

- The exact MetricsQL queries and the step per range (🟠 in #1816's envelope: reported in a batch).
- The detail route's path and payload, following the API's conventions.
- The refresh interval of the detail screen, no faster than the metrics reef's scrape interval, 30s, set as the VMAgent's `scrapeInterval` (`controllers/victoriametrics`) and read by the API from `NEREUS_METRICS_SCRAPE_INTERVAL` (seconds, default 30), which must match it (#2187).
- The M3 tokens of the new components (segmented button, cards, meters), from the portal's `app.css`.
