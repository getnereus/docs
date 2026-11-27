# Collect metrics

See how each Nereid is doing, its passes, failures and how long a pass takes, in the metrics the platform keeps with [VictoriaMetrics](https://docs.victoriametrics.com/).

## Before you start

- A cluster from [Prepare the cluster](../../start/init.md) with `--profile internal-developer-platform`: it brings the metrics Reef with the Nereid `victoriametrics`, which scrapes every Nereid in `nereus-system` and each node's CPU and memory per container.
- `kubectl` reaching that cluster. The query API has no credentials yet, so only the scraper, the Nereus API and a port-forward reach it.

## Steps

### 1. Open vmui

The Mandate `victoriametrics` publishes the in-cluster query address in `status.query.url` ([`nereus mandate get`](../../specs/cli/core.html#mandate-get)). From your machine, forward a port to it, then open `http://localhost:8428/vmui`. The `--context` names the cluster `nereus init` made.

```bash
kubectl port-forward service/vmsingle-nereus 8428:8428 \
  --context k3d-nereus \
  --namespace nereus-system
```

### 2. Count each Nereid's passes

The queries are [MetricsQL](https://docs.victoriametrics.com/metricsql/), a superset of PromQL. Each Nereid built on nereid-sdk serves its metrics with the label `nereid`, taken from its Pod, so no Pod can pose as a Nereid. One series per Nereid: its reconcile passes since it started.

```text
sum by (nereid) (nereus_nereid_reconcile_total)
```

### 3. See which failed, and why

A Nereid that never failed has no error series, so `or` adds a zero for it from the passes, and every Nereid shows up.

```text
sum by (nereid) (nereus_nereid_reconcile_errors_total) or sum by (nereid) (nereus_nereid_reconcile_total) * 0
```

The errors carry a `reason` label, the cause of a failed pass: group by `(nereid, reason)` to see them.

### 4. See how long a pass takes

The duration is a histogram. The 95th percentile over the last five minutes, per Nereid:

```text
histogram_quantile(0.95, sum by (nereid, le) (rate(nereus_nereid_reconcile_duration_seconds_bucket[5m])))
```

## Check it worked

The same port answers the Prometheus query API, for scripts: the first query returns one series per Nereid. A target that fails shows as down, and nothing else stops.

```bash
curl --get \
  --data-urlencode 'query=sum by (nereid) (nereus_nereid_reconcile_total)' \
  http://localhost:8428/api/v1/query
```

## Next

- [Keep a secret](secrets.md), and [release a chart](release.md) that reads it.

## Learn more

- [Inside the metrics Reef](../../reference/metrics-reef.md): what the Nereid installs, what it scrapes and who reaches it.
- [Runtime and profiles](../../concepts/runtime-and-profiles.md): why another Nereid of the metrics Reef would publish the same `status.query.url`.
