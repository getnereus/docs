# 0025. The platform receives metrics from anywhere through the CLI and the Nereus API: declared sources, a spool, late-send alerts with a heartbeat, and machine identities

!!! note "In short"
    Metrics enter only through the Nereus API, with the CLI as the official client: declared sources, a spool, late-send alerts with a heartbeat, and machine identities. Status: Accepted (2026-11-14, by the owner; proposed the same day).

**Status:** Accepted (2026-11-14, by the owner; proposed the same day)

## Context

The owner asked on 2026-11-14 for one official way for the platform to receive metrics from anywhere: external scripts, external pipelines, agents through MCP, a laptop or a server that only drops files in a folder. The first client is the decision metrics of the journeys work (how many decisions wait for the owner, how long each waits), which the owner wants sent through the CLI from day zero, so the channel exists before anything else depends on it. The owner's words: the sending "must be well designed from day zero".

What exists today:

- **The metrics Reef only scrapes.** Its victoriametrics Nereid runs a VMAgent and a VMSingle in `nereus-system`; nothing outside the cluster can write a sample. #783 closes the push endpoint VMAgent opens by default, since any pod could forge series the portal shows as a Nereid's signals (#744); #784 puts vmauth in front of VictoriaMetrics and keeps its import and delete unrouted.
- **The Nereus API is the one door** (ADR 0018), and it has no metrics route.
- **Authentication knows people and the platform's own identity outwards** (ADR 0006: OIDC logins for a `User`, Mandates for a GitHub App), but no machine that signs in to the platform on its own: a systemd unit on a laptop cannot run `nereus login` in a browser.
- **Nereus assumes no vendor:** the store, the registry and the git host are configured, so nothing in this channel may depend on VictoriaMetrics, Keycloak or GitHub.

## Decision

**Metrics enter the platform only through the Nereus API, and the CLI is the official client.** A script, a pipeline, a cron job and an agent all send through `nereus metrics send`, or call the same route the CLI calls; nothing writes to the store directly. The route belongs to the metrics Reef's API group, `metrics.getnereus.dev/v1alpha1` (ADR 0009); no separate intake Reef.

### A source is declared before it sends

A `MetricSource` is the metrics Reef's first kind. It names the metric names a source may write, who may send as it, and how late it may be:

```bash
nereus metrics source create journeys \
  --owner project/nereus \
  --prefix journeys_ \
  --late-after 2h \
  --quiet-after 1d \
  --max-age 7d \
  --machine owner-laptop
```

- **`--prefix`** is the only namespace the source may write: `journeys_decisions_open` is accepted, `nereid_requests_total` is refused. The API refuses a prefix that overlaps another source's (`journeys_` and `journeys_x_`). Reserved for the platform and the tools it runs: `nereus_`, `kube_`, `container_`, `vm_`, `up` and `ALERTS`.
- **`--owner`** is an Organization or a Project (ADR 0015); only a person who may create resources in that owner may create the source.
- **`--late-after`**, **`--quiet-after`** and **`--max-age`** drive the late-send alerts and the accepted delay (below).
- **`--machine`** binds the machine identities that may send as this source; any person allowed in the owner may send too.
- The standard verbs of ADR 0013 apply: `create`, `apply`, `list`, `get`, `delete`. Every source is declared; there is no source made on the fly.

### Sending

```bash
# One sample
nereus metrics send journeys \
  --name journeys_decisions_open \
  --value 3 \
  --label journey=continuous-deploy

# A batch, JSON Lines from a file or a pipe
some-script | nereus metrics send journeys --file -

# Nothing to send: only says the source is alive
nereus metrics send journeys --heartbeat
```

- **The wire format is versioned JSON Lines** (`application/vnd.nereus.metrics.v1+jsonl`), one sample per line: `name`, `value`, `kind` (`counter`, cumulative; `gauge`; or `histogram`, with its buckets), `labels` and `timestamp` (RFC 3339, required). The kinds follow OpenTelemetry's metric data model, so an OTLP entry for pipelines is one more decoder behind the same route. Names and labels follow Prometheus' rules; NaN and infinities are refused.
- **The CLI stamps the timestamp when a sample is made,** never when it is sent. That makes every send idempotent with no key to remember: a retry repeats the same series and timestamp, which the store keeps once, while the same value sent at 10:00 and at 11:00 stays two samples.
- **The API stamps the labels that say where a sample came from:** `source` and the source's owner. A sample that carries either, any label under `getnereus.dev/`, or `job`, `instance`, `namespace` or `nereid`, is refused: an outside sample never passes for a Nereid's signal, the risk #783 closes for VMAgent. Who sent it (a person or a machine) is not a label, so rotating a machine's key or sending once as a person does not split a series; it goes to the audit log.
- **The audit log** keeps one line per request: when, the principal, the source, the samples accepted and refused.
- **The accepted window:** a timestamp no older than the source's `--max-age` (default 7 days, so a laptop off for a long weekend still drains its spool) and no later than 5 minutes ahead (a clock ahead is always an error).
- **Limits, checked before parsing:** request body 1 MiB, after decompression too; line length; 1000 samples per request; 1000 series per source; 60 requests per minute per source. Each is a default the `MetricSource` may override. A refused sample is named in the answer with its reason; the rest of the batch is accepted.
- **The metrics Nereid writes, the API does not.** The API validates and stamps, then hands the batch to the metrics Reef's Nereid, over the cluster network and with a credential of its own (a NetworkPolicy alone is the weakness #784 corrects). Only the Nereid writes to its store; another store (Mimir, a cloud's managed Prometheus) is another Nereid of the same Reef, with the route and the CLI unchanged.
- **MCP:** the Nereus API's `/mcp` exposes `metrics_send`, a tool the Reef declares (ADR 0029), which calls the same route as the person. The portal escapes every label value it shows.

### OpenTelemetry: OTLP on the same route

Pipelines and services that already speak OpenTelemetry send without the CLI, through an OpenTelemetry Collector or an SDK exporter (owner, 2026-11-14):

```yaml
# An OpenTelemetry Collector exporting to Nereus
exporters:
  otlphttp/nereus:
    endpoint: https://api.example.com/v1/metrics/sources/ci-pipeline
    auth:
      authenticator: nereus_machine   # a Machine's token, never a stored API key
```

- **Same route, another decoder:** OTLP/HTTP (`application/x-protobuf` and `application/json`) is told apart by its content type. The source comes from the route and the token, never from an attribute; every rule above (prefix, reserved labels, limits, the accepted window, the audit log, the two clocks) holds the same.
- **Resource and scope attributes become labels,** under the same refusals; an attribute that maps to a reserved label is refused, not renamed.
- **Histograms are accepted,** explicit-bucket and exponential, since latency comes as a histogram from every SDK. The JSON Lines format gains the same kind (`histogram`, with its buckets), so the CLI and OTLP stay equal.
- **Delta temporality is converted to cumulative by the API,** per series, so the store keeps one temporality. A delta series whose start time goes backwards (a restart) starts a new cumulative series, as the OpenTelemetry Collector's delta-to-cumulative processor does.
- **Summaries are refused** with a reason: their quantiles cannot be aggregated, and OpenTelemetry keeps them only for compatibility.

### The spool: a folder of ready files

A machine that only produces files sends them by pointing the CLI at a folder:

```bash
nereus metrics spool /var/spool/nereus-metrics --source journeys
```

- **The folder is `0700`, and a file is ready when it is in `ready/`.** A producer writes `tmp/<name>.jsonl` and renames it into `ready/` once complete, as Maildir does. The CLI reads only regular files up to a size limit and refuses symlinks.
- **`ready/` is the truth:** whatever is in it is still to send. Files go in name order, one request each. The watermark (`state/watermark`, written atomically) records only the last file sent and when; a file found in `ready/` whose name sorts before it is still sent, and the CLI reports it.
- **What each answer does to a file:**

| Answer | The file |
|---|---|
| 2xx, all accepted | moves to `sent/` (kept `--keep 7d`, then deleted) |
| 2xx, part refused | moves to `sent/`; the refused lines go to `rejected/<name>.jsonl` with their reasons |
| 400, 422 | moves to `rejected/` with `<name>.reason` |
| 401, 403 | stays in `ready/`; the run stops and says why |
| 408, 429, 5xx, network | stays in `ready/`, retried with backoff |

- **One stuck file never blocks the queue:** after a number of failed tries the CLI goes on with the next and reports the stuck one in its lag.
- **One run at a time:** the CLI holds a lock on `state/lock`.
- **Every run is a heartbeat:** a run with nothing in `ready/` still makes contact. A one-shot run in a systemd timer is the lightest setup; `--watch` keeps the process up. Both are the same code.
- **Every run reports its own lag:** the age of the oldest file in `ready/` and the count of files in `rejected/` travel with each request, and the API keeps them in the source's status.

### Late-send alerts and the heartbeat

A source has two clocks, both in its `status`, written by the API:

| Clock | Moves on | Past its limit |
|---|---|---|
| `lastSeenTime` | every contact: samples or a heartbeat | `--late-after`: condition `Receiving=False`, reason `Late` (the source is silent) |
| `lastReceivedTime` | accepted samples only | `--quiet-after`, optional: reason `Quiet` (alive, but no data) |

- **A spool that does not drain** is reason `Backlog`: the source makes contact, but its reported lag grows.
- **A source that never sent** counts from its creation, so a timer that never ran is caught.
- **The API compares, not the store:** the logic lives with the `MetricSource`, so it holds with any store.
- **When the API itself was down,** every source's clock restarts when it comes back, and one alert says the API was down, instead of one per source.
- `Quiet` is only for a source that declares data must flow; a source that sends only when something happens leaves `--quiet-after` out.
- Where an alert is delivered (the portal, a push to the phone, a spoken summary) is the notifications question of #278, outside this ADR.

### The source's health, kept as metrics by the platform

A heartbeat writes no sample of the source's, but the contact is not lost: the API records every request as the platform's own series, in the reserved `nereus_` namespace, so a source's health has a history like any other signal.

| Series | What it says |
|---|---|
| `nereus_intake_requests_total{source, kind}` | contacts, `kind` = `samples` or `heartbeat` |
| `nereus_intake_samples_total{source, result}` | samples `accepted` or `refused`, with `reason` on refused |
| `nereus_intake_last_seen_timestamp{source}` | the last contact |
| `nereus_intake_last_received_timestamp{source}` | the last accepted sample |
| `nereus_intake_spool_lag_seconds{source}` | the oldest file still in `ready/`, as the spool reported it |
| `nereus_intake_spool_rejected{source}` | files in `rejected/` |

A source is **healthy** when its condition `Receiving` is `True`: seen within `--late-after`, data within `--quiet-after` when declared, a spool lag under `--late-after`, and refused samples under 5% of the last hour (reason `Refusing` above it). `nereus metrics source get journeys` shows the condition, its reason and the two clocks; the series give the history the portal draws.

### Machine identities

A machine signs in on its own, with no browser and no shared secret, and the same way on every installation.

- **A `Machine` is a kind of core** (`core.getnereus.dev/v1alpha1`), beside `User` (ADR 0006): the platform generates its id, and no authentication Nereid owns it.
- **Its credential is a key pair made on the machine.** `nereus machine create owner-laptop` generates the key locally (mode `0600`, never sent anywhere) and registers only the public key on the `Machine`. Creating a machine needs a person's login, through the device flow of ADR 0006 on a server with no browser.
- **The Nereus API checks the machine, not a login Nereid** (owner, 2026-11-14): the CLI signs a short assertion (`jti` used once, `aud` the API, `exp` of a minute) and the API verifies it against the `Machine`'s public key, then answers with a short token of its own, valid only for the sources that name the machine. It is the model of a GitHub App's JWT, and it holds with Keycloak, Auth0 or any other login Nereid. This is the one exception to "every login is OIDC" of ADR 0006, which points here.
- **A machine can do only what it is bound to:** sending as the sources that name it in `--machine`. It reads nothing and creates nothing else, until another ADR grants more.
- **Revoking is one command,** `nereus machine delete owner-laptop`, and a new key is `nereus machine rotate owner-laptop`; a token already given stays valid until it expires, in minutes.
- **Pipelines, later:** a private key in a pipeline's secret store is a shared secret in practice; a `Machine` that trusts the pipeline's own OIDC issuer and subject (federation, no stored key) is the next step, outside this ADR.

### The order of the work

A walking skeleton, the first data before the riskiest part (owner, 2026-11-14):

1. The `MetricSource` kind, with its prefix and its clocks.
2. The API route, with the person's token that exists today.
3. `nereus metrics send`, with `--heartbeat`.
4. `status.lastSeenTime`, `status.lastReceivedTime` and the conditions.
5. The journeys' decision metrics script sending for real.
6. The spool, one-shot, in a systemd timer.
7. `Machine`: until then, a laptop sends with the refresh token of a device-flow login.
8. OTLP on the same route, with histograms and delta conversion, after `Machine`, since a pipeline signs in as one.

## Prior art

- Prometheus, [When to use the Pushgateway](https://prometheus.io/docs/practices/pushing/): the push channel to avoid, since it keeps series of dead jobs forever and knows nothing of who pushed; the declared source and the late-send alert answer both.
- OpenTelemetry, [Metrics data model](https://opentelemetry.io/docs/specs/otel/metrics/data-model/) and [OTLP/HTTP](https://opentelemetry.io/docs/specs/otlp/#otlphttp): the kinds this ADR uses and the entry for pipelines; the Collector's `deltatocumulativeprocessor`: the conversion the API does.
- Datadog, [Submit metrics](https://docs.datadoghq.com/api/latest/metrics/): an HTTP intake with a key per source and the source stamped by the server.
- Healthchecks.io and Cronitor: the dead man's switch, a job that pings within its period plus a grace time, with no data; Prometheus' `absent_over_time` is the same idea in a rule.
- Maildir ([D. J. Bernstein](https://cr.yp.to/proto/maildir.html)): write in `tmp/`, rename into place, so a reader never sees a partial file.
- Fluent Bit's filesystem buffering and Promtail's positions file: a local spool with a checkpoint, so a restart resumes where it stopped.
- GitHub, [Authenticating as a GitHub App](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-json-web-token-jwt-for-a-github-app): a short JWT signed with a key the App keeps, exchanged for a short token.
- RFC 7523 (JWT profile for OAuth 2.0 client authentication): the shape of the assertion (`iss`, `aud`, `exp`, `jti`).

## Consequences

- The decision metrics of the journeys work become the first source; a later move of the decisions from GitHub to the Nereus API changes their script, not the channel.
- The Nereus API gains the metrics route, the machine sign-in and an audit log; the metrics Reef gains its first kind, and `contracts.REEFS_WITHOUT_KINDS` loses `metrics`.
- The metrics Nereid gains a write endpoint reachable only from the API, with a credential.
- Core gains `Machine`, and ADR 0006 points here for machines.
- OWASP A01 (broken access control: a source writes only its prefix, a machine only its sources), A03 (injection: label values escaped where shown), A04 (insecure design: limits before parsing), A07 (identification and authentication failures: no shared secret, single-use assertions, short tokens) and A09 (logging failures: the audit log) are the categories this touches.

## Open questions

- Where the API keeps the used `jti` values when it runs more than one replica.
- The number of failed tries before the spool goes past a stuck file.

*Origin: the owner's decisions of 2026-11-14 in a session on per-agent journeys and decision envelopes (#1536), with a second opinion read before each. Raw data in Drive `#pontos/raw/2026-11-14/`.*
