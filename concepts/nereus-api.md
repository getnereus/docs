# The Nereus API

The Nereus API is the platform's one door: the CLI, the portal, an IDE and agents talk to it with the person's token, and the Kubernetes API, the Nereids and their tools stay behind it.

## Example

[`nereus whoami`](../specs/cli/reefs/authentication.html#whoami) asks the API's first route, `GET /v1/me`, instead of reading the local token:

```bash
nereus whoami --help
```

``` { .text .output title="output" }
Usage: nereus whoami [OPTIONS]

  Who you are, as the Nereus API answers (GET /v1/me) for the token of nereus
  login, never what the local token says: the login, and the User of Nereus
  behind it (#1645), or that there is none yet.
```

## Overview

<!-- diagram:nereus-api:start (scripts/docs/diagrams) -->
<figure class="diagram nereus-api" markdown="0">
<svg class="rh wide" viewBox="0 0 960 440" role="img" aria-label="The CLI, the portal, agents and IDEs talk to the Nereus API with the person's token; behind it, the Kubernetes API holds the reefs' kinds, the Nereids reconcile them and drive the tools."><rect class="actor" x="0" y="0" width="300" height="48"/><text class="b" x="150" y="29" text-anchor="middle">CLI</text><line class="ln" x1="150" y1="48" x2="150" y2="80"/><polygon class="ah" points="145.1,71.6 154.9,71.6 150,80"/><rect class="actor" x="330" y="0" width="300" height="48"/><text class="b" x="480" y="29" text-anchor="middle">Portal</text><line class="ln" x1="480" y1="48" x2="480" y2="80"/><polygon class="ah" points="475.1,71.6 484.9,71.6 480,80"/><rect class="actor" x="660" y="0" width="300" height="48"/><text class="b" x="810" y="29" text-anchor="middle">Agents, IDE</text><line class="ln" x1="810" y1="48" x2="810" y2="80"/><polygon class="ah" points="805.1,71.6 814.9,71.6 810,80"/><rect class="col" x="0" y="80" width="960" height="56"/><text class="b" x="480" y="104" text-anchor="middle">Nereus API</text><text class="s" x="480" y="124" text-anchor="middle">(api.&lt;domain&gt;, the person's token, one door)</text><rect class="zone" x="0" y="168" width="960" height="192"/><text class="cap" x="24" y="190" text-anchor="start">BEHIND THE DOOR</text><line class="ln" x1="480" y1="136" x2="480" y2="200"/><polygon class="ah" points="475.1,191.6 484.9,191.6 480,200"/><rect class="card" x="24" y="200" width="912" height="56"/><text class="b" x="480" y="224" text-anchor="middle">Kubernetes API</text><text class="s" x="480" y="244" text-anchor="middle">(the reefs' kinds)</text><rect class="card" x="24" y="288" width="912" height="56"/><text class="b" x="480" y="312" text-anchor="middle">Nereids</text><text class="s" x="480" y="332" text-anchor="middle">(they reconcile the kinds)</text><line class="ln" x1="480" y1="256" x2="480" y2="288"/><polygon class="ah" points="475.1,279.6 484.9,279.6 480,288"/><rect class="actor" x="0" y="392" width="960" height="48"/><text class="b" x="480" y="412" text-anchor="middle">Tools</text><text class="s" x="480" y="432" text-anchor="middle">(OpenBao, GitHub, a cloud)</text><line class="ln" x1="480" y1="344" x2="480" y2="392"/><polygon class="ah" points="475.1,383.6 484.9,383.6 480,392"/></svg>
<svg class="rh narrow" viewBox="0 0 360 440" role="img" aria-label="The CLI, the portal, agents and IDEs talk to the Nereus API with the person's token; behind it, the Kubernetes API holds the reefs' kinds, the Nereids reconcile them and drive the tools."><rect class="actor" x="0" y="0" width="112" height="48"/><text class="b" x="56" y="29" text-anchor="middle">CLI</text><line class="ln" x1="56" y1="48" x2="56" y2="80"/><polygon class="ah" points="51.1,71.6 60.9,71.6 56,80"/><rect class="actor" x="124" y="0" width="112" height="48"/><text class="b" x="180" y="29" text-anchor="middle">Portal</text><line class="ln" x1="180" y1="48" x2="180" y2="80"/><polygon class="ah" points="175.1,71.6 184.9,71.6 180,80"/><rect class="actor" x="248" y="0" width="112" height="48"/><text class="b" x="304" y="29" text-anchor="middle">Agents, IDE</text><line class="ln" x1="304" y1="48" x2="304" y2="80"/><polygon class="ah" points="299.1,71.6 308.9,71.6 304,80"/><rect class="col" x="0" y="80" width="360" height="56"/><text class="b" x="180" y="104" text-anchor="middle">Nereus API</text><text class="s" x="180" y="124" text-anchor="middle">(api.&lt;domain&gt;, the person's token, one door)</text><rect class="zone" x="0" y="168" width="360" height="192"/><text class="cap" x="12" y="190" text-anchor="start">BEHIND THE DOOR</text><line class="ln" x1="180" y1="136" x2="180" y2="200"/><polygon class="ah" points="175.1,191.6 184.9,191.6 180,200"/><rect class="card" x="12" y="200" width="336" height="56"/><text class="b" x="180" y="224" text-anchor="middle">Kubernetes API</text><text class="s" x="180" y="244" text-anchor="middle">(the reefs' kinds)</text><rect class="card" x="12" y="288" width="336" height="56"/><text class="b" x="180" y="312" text-anchor="middle">Nereids</text><text class="s" x="180" y="332" text-anchor="middle">(they reconcile the kinds)</text><line class="ln" x1="180" y1="256" x2="180" y2="288"/><polygon class="ah" points="175.1,279.6 184.9,279.6 180,288"/><rect class="actor" x="0" y="392" width="360" height="48"/><text class="b" x="180" y="412" text-anchor="middle">Tools</text><text class="s" x="180" y="432" text-anchor="middle">(OpenBao, GitHub, a cloud)</text><line class="ln" x1="180" y1="344" x2="180" y2="392"/><polygon class="ah" points="175.1,383.6 184.9,383.6 180,392"/></svg>
</figure>
<!-- diagram:nereus-api:end -->

*Clients hold a token, never a kubeconfig; what is behind the door stays behind it.*

## How it works

- It runs in the cluster as `nereus-api` in `nereus-system`, installed by `nereus init` with core; its public name is `api.<domain>`.
- It alone validates the token: the issuer and keys come from the authentication reef's default Mandate, the audience is `nereus-api`, and the Kubernetes apiserver never sees a person's token.
- It acts with its own identity, and decides what the person may do before acting ([Tenancy and access](tenancy-and-access.md)).
- It speaks of reefs and their kinds, never of tools, and reads what the Nereids publish in `status`; what it did not read, it says it did not.
- Command groups move behind it one at a time; the rest keep the kubeconfig as a stand-in, and the check `kubeconfig-ban` refuses any new use outside `nereus init` and the bootstrap.

## Not this

- Not the Kubernetes API: the reefs' kinds live there, but no client reaches it directly.
- Not a proxy to each tool's API: no route names Flux, Keycloak or OpenBao.
- Not the portal: the portal is one client of the API, as the CLI is.

## Next

[Install the CLI](../start/install.md): try it on your own machine.
