# Inside the metrics reef

What the Nereid `victoriametrics` of the metrics reef installs to keep the platform's metrics in [VictoriaMetrics](https://docs.victoriametrics.com/) (Apache-2.0) ([#742](https://github.com/getnereus/nereus/issues/742)). The queries are in [Collect metrics](../guides/reefs/metrics.md).

## The operator

The Nereid asks the release reef for the [VictoriaMetrics operator](https://docs.victoriametrics.com/operator/) (chart `victoria-metrics-operator` 0.68.1, operator v0.75.0, pinned by digest), released by the flux Mandate into the namespace `metrics-system`.

The operator turns a few Kubernetes kinds into running VictoriaMetrics components, as CloudNativePG turns a `Cluster` into PostgreSQL.

## VMSingle

One VictoriaMetrics server, `vmsingle-nereus` in `nereus-system`: it stores the samples on a 2Gi volume for 14 days and answers the Prometheus query API on port 8428. It also serves vmui, the web UI, at `/vmui`.

## VMAgent

The scraper, `vmagent-nereus`, reads the targets the Nereid's scrape objects name and writes the samples to the VMSingle with the Prometheus remote write protocol.

It reads only the scrape objects labelled with the Nereid's name, so another tool's objects never change what it collects.

## What it scrapes

The VMPodScrape `nereids` selects every pod labelled `core.getnereus.dev/metrics: "true"` in `nereus-system`, on its port `http` and path `/metrics`. Each Nereid built on nereid-sdk carries that label ([#741](https://github.com/getnereus/nereus/issues/741)), so no Nereid is ever named.

The label `nereid` of each series comes from the pod's `app.kubernetes.io/name`, never from what the pod serves, so no pod can pose as a Nereid.

The VMNodeScrape `kubelet-cadvisor` reads each node's kubelet at `/metrics/cadvisor`: CPU and memory per container. A target that fails shows as down, and nothing else stops.

The VMPodScrape `kube-state-metrics` reads [kube-state-metrics](https://github.com/kubernetes/kube-state-metrics) ([#2177](https://github.com/getnereus/nereus/issues/2177)), which the Nereid also asks the release reef for: chart 9.1.0, v2.20.0 pinned by digest, in `metrics-system`. The Nereid does not wait for it: it logs a Release not Ready.

It reads only the pods and Deployments of `nereus-system`, through a Role there: no ClusterRole, no Secret, no ConfigMap. It exposes five series: the containers' requests, last termination reason and restarts, and the Deployments' ready and desired replicas.

Its series keep their own `namespace` and `pod` (`honorLabels: true`): those of the pods they describe.

## The contract

The Mandate `victoriametrics` publishes `status.query.url`, the in-cluster address of the query API, and its Ready condition; `nereus mandate get victoriametrics` shows both. It names no backend: another Nereid of the metrics reef would publish the same field.

## Who reaches it

The query API has no credentials yet. A NetworkPolicy, applied by `nereus nereid apply` and not by the Nereid, lets only the VMAgent and the Nereus API reach port 8428; a `kubectl port-forward` is not subject to it.

Deleting series takes a random key nobody is given (`-deleteAuthKey`, from the Secret `victoriametrics-delete-key`). An admission policy holds every object the Nereid writes to its name and its whole spec.

## The proof

`make scene-metrics` installs the reef on a throwaway cluster and runs the three queries of [Collect metrics](../guides/reefs/metrics.md), expecting one series per Nereid.
