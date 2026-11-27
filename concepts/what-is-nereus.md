# What Nereus is

Nereus is a composable API platform: Reefs add the APIs, Nereids look after them, both installed at runtime, and one API and one CLI serve them all.

## Example

`nereus --help` groups the commands: the platform's own, the model's, and one group per Reef the installation knows:

```bash
nereus --help
```

``` { .text .output title="output" }
Usage: nereus [OPTIONS] COMMAND [ARGS]...

  nereus: a composable API platform: reefs add the APIs, Nereids look after
  them, installed at runtime.

Model:
  mandate         Mandates: each binds one reef to one Nereid.
  nereid          Nereids: the controllers that look after reefs.
  reef            Reefs: the capabilities of the platform, each an API group.
  user            Users: one per person, whatever the login.

Reefs:
  authentication  Reef authentication, looked after by nereid keycloak.
  release         Reef release, looked after by nereid flux.
  secrets         Reef secrets, looked after by nereid openbao.
```

## Overview

<!-- diagram:architecture:start (scripts/docs/diagrams) -->
<figure class="diagram architecture" markdown="0">
<svg class="rh wide" viewBox="0 0 960 612" role="img" aria-label="One Nereus installation: clients ask the control plane (the Nereus API, its Reefs and Nereids), which reconciles the environments where workloads, databases and message streams run, beside images, secrets and outside services, on any infrastructure."><rect class="actor" x="24" y="0" width="320" height="44"/><text class="b" x="184" y="28" text-anchor="middle">IDE, CLI, Portal, Agents</text><rect class="zone" x="0" y="64" width="700" height="410"/><text class="h" x="24" y="98" text-anchor="start">Nereus installation</text><line class="ln" x1="300" y1="44" x2="300" y2="128"/><polygon class="ah" points="295.1,119.6 304.9,119.6 300,128"/><text class="lbl" x="312" y="104" text-anchor="start">Ask</text><rect class="card" x="24" y="128" width="320" height="322"/><text class="h2" x="48" y="160" text-anchor="start">Control plane</text><rect class="col" x="48" y="178" width="272" height="40"/><text class="s" x="184" y="204" text-anchor="middle">Nereus API</text><rect class="col" x="48" y="228" width="272" height="40"/><text class="s" x="184" y="254" text-anchor="middle">Reefs, one per plane</text><rect class="col" x="48" y="278" width="272" height="40"/><text class="s" x="184" y="304" text-anchor="middle">Nereids</text><line class="ln" x1="184" y1="322" x2="184" y2="380"/><polygon class="ah" points="179.1,371.6 188.9,371.6 184,380"/><polygon class="ah" points="179.1,330.4 188.9,330.4 184,322"/><ellipse class="cyl" cx="184" cy="392" rx="34" ry="9"/><path class="cyl" d="M150,392 V412 A34,9 0 0 0 218,412 V392"/><text class="s" x="184" y="440" text-anchor="middle">cluster state</text><rect class="card" x="368" y="128" width="300" height="322"/><text class="h2" x="392" y="160" text-anchor="start">Environments</text><rect class="focus" x="392" y="178" width="252" height="160"/><text class="b" x="410" y="204" text-anchor="start">Workloads</text><rect class="col" x="410" y="218" width="216" height="40"/><text class="s" x="518" y="244" text-anchor="middle">apps from a golden path</text><rect class="col" x="410" y="270" width="216" height="40"/><text class="s" x="518" y="296" text-anchor="middle">their routes</text><rect class="col" x="392" y="348" width="252" height="38"/><text class="s" x="518" y="373" text-anchor="middle">Databases</text><rect class="col" x="392" y="394" width="252" height="38"/><text class="s" x="518" y="419" text-anchor="middle">Message streams</text><line class="ln" x1="340" y1="258" x2="372" y2="258"/><polygon class="ah" points="363.6,253.1 363.6,262.9 372,258"/><polygon class="ah" points="348.4,253.1 348.4,262.9 340,258"/><text class="lbl" x="356" y="290" text-anchor="middle">reconcile</text><rect class="actor" x="730" y="64" width="230" height="200"/><ellipse class="cyl" cx="845" cy="122" rx="34" ry="9"/><path class="cyl" d="M811,122 V150 A34,9 0 0 0 879,150 V122"/><path class="cyl" d="M811,136 A34,9 0 0 0 879,136"/><text class="s" x="845" y="194" text-anchor="middle">Images and secrets</text><text class="m" x="845" y="214" text-anchor="middle">(registry, vault)</text><line class="ln" x1="702" y1="164" x2="728" y2="164"/><polygon class="ah" points="719.6,159.1 719.6,168.9 728,164"/><polygon class="ah" points="710.4,159.1 710.4,168.9 702,164"/><rect class="actor" x="730" y="274" width="230" height="200"/><circle class="cyl" cx="845" cy="340" r="26"/><ellipse class="cyl" cx="845" cy="340" rx="11" ry="26"/><line class="ln" x1="819" y1="340" x2="871" y2="340"/><text class="s" x="845" y="404" text-anchor="middle">Outside</text><text class="m" x="845" y="424" text-anchor="middle">(Cloudflare, GitHub, the cloud)</text><line class="ln" x1="702" y1="374" x2="728" y2="374"/><polygon class="ah" points="719.6,369.1 719.6,378.9 728,374"/><polygon class="ah" points="710.4,369.1 710.4,378.9 702,374"/><rect class="dash" x="0" y="510" width="960" height="64"/><rect class="actor" x="10" y="520" width="180" height="44"/><text class="s" x="100" y="548" text-anchor="middle">Laptop</text><rect class="actor" x="200" y="520" width="180" height="44"/><text class="s" x="290" y="548" text-anchor="middle">Virtual</text><rect class="actor" x="390" y="520" width="180" height="44"/><text class="s" x="480" y="548" text-anchor="middle">Private cloud</text><rect class="actor" x="580" y="520" width="180" height="44"/><text class="s" x="670" y="548" text-anchor="middle">Public cloud</text><rect class="actor" x="770" y="520" width="180" height="44"/><text class="s" x="860" y="548" text-anchor="middle">Edge</text><line class="ln" x1="350" y1="476" x2="350" y2="508"/><polygon class="ah" points="345.1,499.6 354.9,499.6 350,508"/><polygon class="ah" points="345.1,484.4 354.9,484.4 350,476"/><line class="ln" x1="845" y1="476" x2="845" y2="508"/><polygon class="ah" points="840.1,499.6 849.9,499.6 845,508"/><polygon class="ah" points="840.1,484.4 849.9,484.4 845,476"/><line class="ln" x1="480" y1="574" x2="508" y2="598"/><text class="s" x="516" y="604" text-anchor="start">Underlying infrastructure</text></svg>
<svg class="rh narrow" viewBox="0 0 360 884" role="img" aria-label="One Nereus installation: clients ask the control plane (the Nereus API, its Reefs and Nereids), which reconciles the environments where workloads, databases and message streams run, beside images, secrets and outside services, on any infrastructure."><rect class="actor" x="0" y="0" width="360" height="44"/><text class="b" x="180" y="28" text-anchor="middle">IDE, CLI, Portal, Agents</text><line class="ln" x1="180" y1="44" x2="180" y2="76"/><polygon class="ah" points="175.1,67.6 184.9,67.6 180,76"/><text class="lbl" x="192" y="66" text-anchor="start">Ask</text><rect class="zone" x="0" y="76" width="360" height="496"/><text class="h" x="12" y="106" text-anchor="start">Nereus installation</text><rect class="card" x="12" y="120" width="336" height="172"/><text class="h2" x="28" y="146" text-anchor="start">Control plane</text><rect class="col" x="28" y="160" width="304" height="38"/><text class="s" x="180" y="184" text-anchor="middle">Nereus API</text><rect class="col" x="28" y="206" width="304" height="38"/><text class="s" x="180" y="230" text-anchor="middle">Reefs, one per plane</text><rect class="col" x="28" y="252" width="304" height="38"/><text class="s" x="180" y="276" text-anchor="middle">Nereids</text><line class="ln" x1="180" y1="296" x2="180" y2="322"/><polygon class="ah" points="175.1,313.6 184.9,313.6 180,322"/><polygon class="ah" points="175.1,304.4 184.9,304.4 180,296"/><text class="lbl" x="192" y="314" text-anchor="start">reconcile</text><rect class="card" x="12" y="326" width="336" height="232"/><text class="h2" x="28" y="352" text-anchor="start">Environments</text><rect class="col" x="28" y="366" width="304" height="38"/><text class="s" x="180" y="390" text-anchor="middle">apps from a golden path</text><rect class="col" x="28" y="412" width="304" height="38"/><text class="s" x="180" y="436" text-anchor="middle">their routes</text><rect class="col" x="28" y="458" width="304" height="38"/><text class="s" x="180" y="482" text-anchor="middle">Databases</text><rect class="col" x="28" y="504" width="304" height="38"/><text class="s" x="180" y="528" text-anchor="middle">Message streams</text><rect class="actor" x="0" y="584" width="360" height="58"/><text class="b" x="12" y="608" text-anchor="start">Images and secrets</text><text class="m" x="12" y="628" text-anchor="start">registry, vault</text><rect class="actor" x="0" y="650" width="360" height="58"/><text class="b" x="12" y="674" text-anchor="start">Outside</text><text class="m" x="12" y="694" text-anchor="start">Cloudflare, GitHub, the cloud</text><text class="cap" x="0" y="730" text-anchor="start">UNDERLYING INFRASTRUCTURE</text><rect class="actor" x="0" y="740" width="174" height="40"/><text class="s" x="87" y="766" text-anchor="middle">Laptop</text><rect class="actor" x="186" y="740" width="174" height="40"/><text class="s" x="273" y="766" text-anchor="middle">Virtual</text><rect class="actor" x="0" y="788" width="174" height="40"/><text class="s" x="87" y="814" text-anchor="middle">Private cloud</text><rect class="actor" x="186" y="788" width="174" height="40"/><text class="s" x="273" y="814" text-anchor="middle">Public cloud</text><rect class="actor" x="0" y="836" width="174" height="40"/><text class="s" x="87" y="862" text-anchor="middle">Edge</text></svg>
</figure>
<!-- diagram:architecture:end -->

*One installation: the control plane reconciles the environments, beside the services it uses, on any infrastructure.*

## How it works

- The engine is `core`, the kinds `Reef`, `Nereid`, `Mandate` and `Profile`, and nothing else; the words are in [Reef, Nereid and Mandate](model.md).
- Every capability arrives at runtime as a Reef, and a Nereid fills it with the tool you pick ([Runtime install and profiles](runtime-and-profiles.md)).
- The CLI, the portal and agents go through one door, [the Nereus API](nereus-api.md), and never name a tool.
- Swapping a tool means adding another Nereid to the Reef and moving its default Mandate: no command, client or app declaration changes.
- Whose each thing is, and who may act on it, belongs to the platform itself ([Tenancy and access](tenancy-and-access.md)).

## Not this

- Not only an Internal Developer Platform: that is one profile, `internal-developer-platform`; a Reef can serve any recurring knowledge work.
- Not a portal: the portal is one Reef, `portal`, and one client of the API.
- Not a wrapper around one tool: Flux, Keycloak or OpenBao stay behind a Nereid, and a Reef outlives the tool.
- Not a replacement for Kubernetes: it runs on a cluster, and each Reef is an API group there.

## Next

[Reef, Nereid and Mandate](model.md): the three words the rest of the docs use.
