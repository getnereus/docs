# Reef, Nereid and Mandate

A Reef is a capability of the platform, a Nereid is the controller that looks after it, and a Mandate binds one Reef to one Nereid.

## Example

`nereus --help` lists each Reef installed with the Nereid that looks after it:

``` { .text .output title="output" }
Reefs:
  release         Reef release, looked after by nereid flux.
  secrets         Reef secrets, looked after by nereid openbao.
```

The secrets Reef adds the kinds `Vault` and `Secret` and the commands `nereus secrets ...`; the Mandate `default` says that `openbao` keeps them.

## Overview

<!-- diagram:model:start (scripts/docs/diagrams) -->
<figure class="diagram model" markdown="0">
<svg class="rh wide" viewBox="0 0 960 240" role="img" aria-label="nereus secrets create reaches the Reef secrets, an API group; the Mandate default binds it to the Nereid openbao, a controller, which drives the tool OpenBao."><rect class="actor" x="0" y="56" width="220" height="56"/><text class="b" x="110" y="89" text-anchor="middle">nereus secrets create</text><rect class="zone" x="260" y="0" width="500" height="240"/><text class="h" x="284" y="34" text-anchor="start">Nereus installation</text><rect class="card" x="284" y="56" width="200" height="56"/><text class="b" x="384" y="80" text-anchor="middle">Reef secrets</text><text class="s" x="384" y="100" text-anchor="middle">(an API group)</text><line class="ln" x1="220" y1="84" x2="284" y2="84"/><polygon class="ah" points="275.6,79.1 275.6,88.9 284,84"/><rect class="card" x="284" y="160" width="200" height="56"/><text class="b" x="384" y="184" text-anchor="middle">Mandate default</text><text class="s" x="384" y="204" text-anchor="middle">(binds the two)</text><line class="ln" x1="384" y1="160" x2="384" y2="112"/><polygon class="ah" points="379.1,120.4 388.9,120.4 384,112"/><rect class="card" x="524" y="160" width="212" height="56"/><text class="b" x="630" y="184" text-anchor="middle">Nereid openbao</text><text class="s" x="630" y="204" text-anchor="middle">(a controller)</text><line class="ln" x1="484" y1="188" x2="524" y2="188"/><polygon class="ah" points="515.6,183.1 515.6,192.9 524,188"/><rect class="actor" x="800" y="160" width="160" height="56"/><text class="b" x="880" y="184" text-anchor="middle">OpenBao</text><text class="s" x="880" y="204" text-anchor="middle">(the tool)</text><line class="ln" x1="736" y1="188" x2="800" y2="188"/><polygon class="ah" points="791.6,183.1 791.6,192.9 800,188"/></svg>
<svg class="rh narrow" viewBox="0 0 360 446" role="img" aria-label="nereus secrets create reaches the Reef secrets, an API group; the Mandate default binds it to the Nereid openbao, a controller, which drives the tool OpenBao."><rect class="actor" x="0" y="0" width="360" height="50"/><text class="b" x="180" y="30" text-anchor="middle">nereus secrets create</text><line class="ln" x1="180" y1="50" x2="180" y2="120"/><polygon class="ah" points="175.1,111.6 184.9,111.6 180,120"/><rect class="zone" x="0" y="76" width="360" height="282"/><text class="h" x="12" y="106" text-anchor="start">Nereus installation</text><rect class="card" x="12" y="120" width="336" height="56"/><text class="b" x="180" y="144" text-anchor="middle">Reef secrets</text><text class="s" x="180" y="164" text-anchor="middle">(an API group)</text><rect class="card" x="12" y="208" width="336" height="56"/><text class="b" x="180" y="232" text-anchor="middle">Mandate default</text><text class="s" x="180" y="252" text-anchor="middle">(binds the two)</text><line class="ln" x1="180" y1="208" x2="180" y2="176"/><polygon class="ah" points="175.1,184.4 184.9,184.4 180,176"/><rect class="card" x="12" y="288" width="336" height="56"/><text class="b" x="180" y="312" text-anchor="middle">Nereid openbao</text><text class="s" x="180" y="332" text-anchor="middle">(a controller)</text><line class="ln" x1="180" y1="264" x2="180" y2="288"/><polygon class="ah" points="175.1,279.6 184.9,279.6 180,288"/><rect class="actor" x="0" y="390" width="360" height="56"/><text class="b" x="180" y="414" text-anchor="middle">OpenBao</text><text class="s" x="180" y="434" text-anchor="middle">(the tool)</text><line class="ln" x1="180" y1="344" x2="180" y2="390"/><polygon class="ah" points="175.1,381.6 184.9,381.6 180,390"/></svg>
</figure>
<!-- diagram:model:end -->

*The CLI speaks to the Reef; the Mandate names the Nereid that does the work with its tool.*

## How it works

- A Reef is an API group, `<reef>.getnereus.dev`, with its own kinds; [`nereus reef apply`](../specs/cli/core.html#reef-apply) adds one at runtime.
- A Nereid is a Kubernetes controller that reconciles the Reef's objects and writes their `status`.
- A Mandate binds one Reef to one Nereid; one Mandate per Reef is the default, and its commands go there.
- Several Nereids can look after one Reef (`keycloak` or `auth0` for authentication): you pick one per Mandate.
- Each Reef adds its own commands to the CLI, so `nereus --help` grows with the installation.

## Not this

- A Reef is not a Helm chart: it is the API; the Nereid brings the software behind it.
- A Nereid is not the tool itself: `openbao` is the controller, OpenBao is what it drives.

## Next

[Runtime install and profiles](runtime-and-profiles.md): how Reefs and Nereids arrive in a running installation.
