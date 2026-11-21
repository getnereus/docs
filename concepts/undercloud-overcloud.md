# Undercloud and overcloud

The undercloud is the local k3d cluster that seeds an installation and bootstraps its cloud; the overcloud is the cloud cluster, AKS first, the platform then moves into, still as one installation.

[planned #61]

## Example

A cloud in the settings file makes `nereus init` create the undercloud, `tailwind-undercloud`, instead of a plain local cluster:

```yaml
apiVersion: core.getnereus.dev/v1alpha1
kind: InitConfig
spec:
  cloud: azure
---
apiVersion: core.getnereus.dev/v1alpha1
kind: Installation
metadata:
  name: tailwind
spec:
  alias: tailwind
```

## Overview

<!-- diagram:undercloud:start (scripts/docs/diagrams) -->
<figure class="diagram undercloud" markdown="0">
<svg class="rh wide" viewBox="0 0 960 322" role="img" aria-label="Your az login runs the bootstrap plan of the undercloud, a local k3d cluster that seeds the installation; the pivot moves the same installation to the overcloud, AKS, both on Azure."><rect class="actor" x="0" y="72" width="180" height="56"/><text class="b" x="90" y="105" text-anchor="middle">your az login</text><rect class="zone" x="220" y="0" width="320" height="230"/><text class="h" x="244" y="34" text-anchor="start">Undercloud</text><text class="m" x="368" y="34" text-anchor="start">(k3d, on your machine)</text><rect class="card" x="244" y="72" width="272" height="56"/><text class="b" x="380" y="96" text-anchor="middle">Nereus installation</text><text class="s" x="380" y="116" text-anchor="middle">(seeded here)</text><rect class="card" x="244" y="148" width="272" height="56"/><text class="b" x="380" y="172" text-anchor="middle">bootstrap plan</text><text class="s" x="380" y="192" text-anchor="middle">(issuer, identity)</text><path class="ln" d="M90,128 L90,176 L244,176"/><polygon class="ah" points="235.6,171.1 235.6,180.9 244,176"/><rect class="zone" x="620" y="0" width="340" height="230"/><text class="h" x="644" y="34" text-anchor="start">Overcloud</text><text class="m" x="760" y="34" text-anchor="start">(AKS)</text><rect class="card" x="644" y="72" width="292" height="56"/><text class="b" x="790" y="96" text-anchor="middle">Nereus installation</text><text class="s" x="790" y="116" text-anchor="middle">(the same one, moved)</text><line class="ln" x1="516" y1="100" x2="644" y2="100"/><polygon class="ah" points="635.6,95.1 635.6,104.9 644,100"/><text class="lbl" x="580" y="90" text-anchor="middle">pivot</text><rect class="dash" x="0" y="270" width="960" height="52"/><text class="b" x="480" y="301" text-anchor="middle">Azure</text><line class="ln" x1="380" y1="204" x2="380" y2="270"/><polygon class="ah" points="375.1,261.6 384.9,261.6 380,270"/><line class="ln" x1="790" y1="128" x2="790" y2="270"/><polygon class="ah" points="785.1,261.6 794.9,261.6 790,270"/></svg>
<svg class="rh narrow" viewBox="0 0 360 476" role="img" aria-label="Your az login runs the bootstrap plan of the undercloud, a local k3d cluster that seeds the installation; the pivot moves the same installation to the overcloud, AKS, both on Azure."><rect class="actor" x="0" y="0" width="360" height="44"/><text class="b" x="180" y="27" text-anchor="middle">your az login</text><line class="ln" x1="180" y1="44" x2="180" y2="76"/><polygon class="ah" points="175.1,67.6 184.9,67.6 180,76"/><rect class="zone" x="0" y="76" width="360" height="178"/><text class="h" x="12" y="106" text-anchor="start">Undercloud</text><text class="m" x="348" y="106" text-anchor="end">(k3d, your machine)</text><rect class="card" x="12" y="120" width="336" height="56"/><text class="b" x="180" y="144" text-anchor="middle">Nereus installation</text><text class="s" x="180" y="164" text-anchor="middle">(seeded here)</text><rect class="card" x="12" y="184" width="336" height="56"/><text class="b" x="180" y="208" text-anchor="middle">bootstrap plan</text><text class="s" x="180" y="228" text-anchor="middle">(issuer, identity)</text><line class="ln" x1="180" y1="254" x2="180" y2="290"/><polygon class="ah" points="175.1,281.6 184.9,281.6 180,290"/><text class="lbl" x="192" y="278" text-anchor="start">pivot</text><rect class="zone" x="0" y="290" width="360" height="114"/><text class="h" x="12" y="320" text-anchor="start">Overcloud</text><text class="m" x="348" y="320" text-anchor="end">(AKS)</text><rect class="card" x="12" y="334" width="336" height="56"/><text class="b" x="180" y="358" text-anchor="middle">Nereus installation</text><text class="s" x="180" y="378" text-anchor="middle">(the same one, moved)</text><line class="ln" x1="180" y1="404" x2="180" y2="428"/><polygon class="ah" points="175.1,419.6 184.9,419.6 180,428"/><rect class="dash" x="0" y="428" width="360" height="48"/><text class="b" x="180" y="457" text-anchor="middle">Azure</text></svg>
</figure>
<!-- diagram:undercloud:end -->

*The undercloud gets the cloud to trust it, then hands the platform to the overcloud.*

## How it works

- [`nereus init --target azure`](../specs/cli/core.html#init-target) computes the cluster's OIDC issuer from the installation's id before the cluster exists, then installs the `cloud` reef and its `azure` Nereid.
- The Nereid plans the bootstrap (the names, the issuer storage, the issuer documents, the first identity); the CLI shows the plan and runs it with your own login once you approve.
- From then on the cloud trusts the cluster's tokens through workload identity federation, so the platform keeps no secret.
- The pivot moves the platform to the overcloud, as Cluster API's `clusterctl move` does, moves the federated credential to the overcloud's issuer, then deletes the undercloud [planned #61].
- Both are one installation: the same name, id and identities; only the cluster role label, `core.getnereus.dev/cluster-role`, stays with each cluster.

## Not this

- Not two installations, nor staging and production: one platform on two clusters, one after the other.
- Not a management cluster kept forever: the undercloud is deleted after the pivot.
- Not needed on a laptop: a plain `nereus init` with no cloud makes a cluster named `nereus`, with no undercloud role.

## Next

[Tenancy and access](tenancy-and-access.md): whose each thing is, and who may do what.
