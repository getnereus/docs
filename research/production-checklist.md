# Production-grade checklist

!!! note "Recommendations, not a gate"
    This page is a reference for opportunities Nereus may take up, one day or never. It is not a list of requirements: no slice, Nereid, Reef or PR has to tick these items, and no check enforces them. When one of them becomes work, it starts as an issue and, if it is a new capability, as an API group ([API groups](../agent/api-groups.md)).

The list follows the production-grade infrastructure checklist in Yevgeniy Brikman's book *Terraform: Up & Running: Writing Infrastructure as Code*, Second Edition. The descriptions below are our own words; the tools are examples, not choices. Where a task fits the model, a short note says how it could map to a Reef or a Nereid ([The CLI design](../agent/cli.md), ADR 0002 (the conceptual model: Reefs, Nereids, Mandates)); those notes are ideas, not decisions.

## Install

Get the software and everything it depends on onto the machine or into the image, in a way that can be repeated.

- **Example tools:** Bash, Ansible, Chef, Puppet, container images built by Docker or Buildpacks.
- **In Nereus:** a Nereid ships as a container image, so installing it is pulling that image; the `release` Reef (with the `flux` Nereid) already installs Helm charts.

## Configure

Set how the software behaves when it runs: ports, certificates, how services find each other, which node leads, how data is replicated.

- **Example tools:** Ansible, Chef, Puppet, Helm values, Kustomize, ConfigMaps.
- **In Nereus:** the `spec` of a Reef's object carries the configuration the API writes, and the Nereid turns it into the tool's own settings (ADR 0005 (one writer per field: the API writes `spec`, the Nereid writes `status`)).

## Provision

Create the infrastructure itself: servers, networks, load balancers, firewall rules, identities and their permissions.

- **Example tools:** Terraform, OpenTofu, CloudFormation, Crossplane, Pulumi.
- **In Nereus:** the `cloud` Reef (spec 0005) and the `environment` Reef are where provisioning lands; a Terraform or Crossplane Nereid could serve them behind a Mandate, so the tool can be swapped.

## Deploy

Put the service on top of the infrastructure and roll out new versions without taking it down, gradually or side by side.

- **Example tools:** Kubernetes, Helm, Flux, Argo CD, Argo Rollouts, Flagger, ECS.
- **In Nereus:** the `release` Reef; blue-green, rolling and canary strategies could become fields of a release, served by a Nereid that wraps Flagger or Argo Rollouts.

## High availability

Keep working when a process, a server, a service, a data centre or a whole region fails.

- **Example tools:** replicas across zones, multi-region replication, load balancers, auto scaling, PodDisruptionBudgets.
- **In Nereus:** an availability level could be a field of an `environment` or a release, which the Nereid translates into replicas, zones and disruption budgets; the chaos step of the walkthrough ([When the Nereid stops](../guides/troubleshoot/nereid-stops.md)) is the first taste of it.

## Scalability

Grow and shrink with the load, by adding more copies (out) or bigger machines (up).

- **Example tools:** Horizontal Pod Autoscaler, KEDA, Karpenter, Cluster Autoscaler, sharding, caches.
- **In Nereus:** scaling rules could sit beside availability in the same objects; KEDA fits well where an event bus (the `messaging` Reef) drives the load.

## Performance

Use CPU, memory, disk, network and GPU well, and know it from measurement: profiling, benchmarks, load tests, query tuning.

- **Example tools:** k6, JMeter, Locust, pprof, py-spy, Pyroscope, Dynatrace.
- **In Nereus:** the init time SLO (spec 0004) is already one measured target; a load test could become a command of a Reef, run against an Instance before a release is promoted.

## Networking

Addresses, ports, DNS, how services discover each other, firewalls, and how people reach machines (SSH, VPN).

- **Example tools:** VPCs, security groups, CoreDNS, ExternalDNS, Cilium, Tailscale, WireGuard, Cloudflare Tunnel.
- **In Nereus:** the planned `edge` Reef with a `cloudflare` Nereid publishes a hostname as a Route ([Publish at a hostname](../guides/operate/edge.md)); DNS and private access could follow as Reefs of their own.

## Security

Encrypt data on the wire and at rest, know who is calling and what they may do, keep secrets out of code, harden what runs.

- **Example tools:** cert-manager, Let's Encrypt, OpenBao, Vault, KMS, Keycloak, Kyverno, Trivy, CIS benchmarks.
- **In Nereus:** the `secrets` Reef (the `openbao` Nereid, with client-side encryption by the CLI) and the `authentication` Reef (the `keycloak` Nereid) cover part of it already; certificates and policy could be Reefs too. "Security from the first slice" is already a pillar ([Rules](../agent/rules.md)).

## Metrics

Measure whether the system is up and doing its job, from the business down to the server, trace requests, and alert a person when it matters.

- **Example tools:** Prometheus, Grafana, OpenTelemetry, Tempo, Alertmanager, Datadog, Honeycomb.
- **In Nereus:** an `observability` Reef could let a Nereid publish its metrics and traces the same way whatever the backend; the `notifications` Reef idea (#278 (spoken summaries as notifications)) could carry the alerts.

## Logs

Keep logs from filling the disk, and gather them in one place where they can be searched.

- **Example tools:** Fluent Bit, Vector, Loki, OpenSearch, the ELK stack, CloudWatch Logs.
- **In Nereus:** the same `observability` Reef could take logs, with a Loki or OpenSearch Nereid behind a Mandate.

## Backup and restore

Copy databases, caches and other data on a schedule, keep a copy in another region or account, and prove that it restores.

- **Example tools:** Velero, CloudNativePG backups, restic, snapshots of managed databases, cross-region replication.
- **In Nereus:** a `backup` Reef could ask for a schedule and a retention on an Instance, served by a Velero Nereid; a restore test could be one of its commands.

## Cost optimization

Pick the right machine sizes, use spot and reserved capacity, scale down when idle, and remove what nobody uses.

- **Example tools:** OpenCost, Kubecost, Karpenter, spot and reserved instances, auto scaling, cloud-nuke.
- **In Nereus:** costs are a lever among the pillars ([Vision](../vision.md)); the `cost` Reef idea (#277 (the AI-usage Nereid of the `cost` Reef)) could grow to infrastructure costs with an OpenCost Nereid.

## Documentation

Write down the code, the architecture and the practices, and keep runbooks for the incidents that will happen.

- **Example tools:** MkDocs, Backstage TechDocs, ADRs, runbooks, READMEs.
- **In Nereus:** this site, the ADRs and the walkthrough already do much of it; a Reef or Nereid could publish its own runbook next to its commands.

## Tests

Test the infrastructure code automatically, on every change and on a schedule.

- **Example tools:** Terratest, Chainsaw, kuttl, InSpec, conftest, pytest.
- **In Nereus:** the scene (`make scene`) and Nereid conformance (spec 0003) are the start; conformance tests could become what every Nereid passes before a Mandate may point at it.

## Learn more

- Yevgeniy Brikman, *Terraform: Up & Running: Writing Infrastructure as Code*, Second Edition: the production-grade infrastructure checklist this page follows, read from a one-page copy of the checklist on 2026-10-29.
