# Runtime install and profiles

Nereus installs its capabilities at runtime: `nereus init` lays down the engine, `core`, and a profile is a named list of Reefs, Nereids and Mandates applied on top of it.

## Example

[`nereus profile describe`](../specs/cli/core.html#profile-describe) shows what a profile installs, in order, each Nereid with its Reef and its Mandate:

```bash
nereus profile describe secrets
```

``` { .text .output title="output" }
NEREID   REEF     MANDATE            REQUIRED BY
openbao  secrets  default (default)  -
```

## Overview

<!-- diagram:runtime:start (scripts/docs/diagrams) -->
<figure class="diagram runtime" markdown="0">
<svg class="rh wide" viewBox="0 0 960 320" role="img" aria-label="nereus init lays down core, the engine, and a profile; the Nereid thetis installs the profile's Reefs, Nereids and Mandates, which a person can also apply one at a time."><rect class="actor" x="0" y="63" width="200" height="50"/><text class="b" x="100" y="93" text-anchor="middle">nereus init</text><rect class="zone" x="240" y="0" width="720" height="320"/><text class="h" x="264" y="34" text-anchor="start">Nereus installation</text><rect class="card" x="264" y="56" width="210" height="64"/><text class="b" x="369" y="84" text-anchor="middle">core</text><text class="s" x="369" y="104" text-anchor="middle">(the engine)</text><line class="ln" x1="200" y1="88" x2="264" y2="88"/><polygon class="ah" points="255.6,83.1 255.6,92.9 264,88"/><rect class="card" x="264" y="150" width="210" height="64"/><text class="b" x="369" y="178" text-anchor="middle">Profile</text><text class="s" x="369" y="198" text-anchor="middle">(picked at init)</text><path class="ln" d="M100,113 L100,182 L264,182"/><polygon class="ah" points="255.6,177.1 255.6,186.9 264,182"/><rect class="card" x="514" y="150" width="190" height="64"/><text class="b" x="609" y="178" text-anchor="middle">Nereid thetis</text><text class="s" x="609" y="198" text-anchor="middle">(the installer)</text><line class="ln" x1="474" y1="182" x2="514" y2="182"/><polygon class="ah" points="505.6,177.1 505.6,186.9 514,182"/><rect class="card" x="744" y="56" width="192" height="244"/><text class="h2" x="840" y="84" text-anchor="middle">Installed</text><line class="ln" x1="704" y1="182" x2="744" y2="182"/><polygon class="ah" points="735.6,177.1 735.6,186.9 744,182"/><rect class="col" x="760" y="100" width="160" height="40"/><text class="s" x="840" y="125" text-anchor="middle">Reefs</text><rect class="col" x="760" y="148" width="160" height="40"/><text class="s" x="840" y="173" text-anchor="middle">Nereids</text><rect class="col" x="760" y="196" width="160" height="40"/><text class="s" x="840" y="221" text-anchor="middle">Mandates</text><rect class="actor" x="0" y="240" width="210" height="60"/><text class="b" x="105" y="266" text-anchor="middle">nereus reef apply</text><text class="s" x="105" y="286" text-anchor="middle">(and nereid apply, one at a time)</text><line class="ln" x1="210" y1="270" x2="744" y2="270"/><polygon class="ah" points="735.6,265.1 735.6,274.9 744,270"/></svg>
<svg class="rh narrow" viewBox="0 0 360 620" role="img" aria-label="nereus init lays down core, the engine, and a profile; the Nereid thetis installs the profile's Reefs, Nereids and Mandates, which a person can also apply one at a time."><rect class="actor" x="0" y="0" width="360" height="44"/><text class="b" x="180" y="27" text-anchor="middle">nereus init</text><line class="ln" x1="180" y1="44" x2="180" y2="76"/><polygon class="ah" points="175.1,67.6 184.9,67.6 180,76"/><rect class="zone" x="0" y="76" width="360" height="454"/><text class="h" x="12" y="106" text-anchor="start">Nereus installation</text><rect class="card" x="12" y="120" width="336" height="56"/><text class="b" x="180" y="144" text-anchor="middle">core</text><text class="s" x="180" y="164" text-anchor="middle">(the engine)</text><rect class="card" x="12" y="184" width="336" height="56"/><text class="b" x="180" y="208" text-anchor="middle">Profile</text><text class="s" x="180" y="228" text-anchor="middle">(picked at init)</text><line class="ln" x1="180" y1="240" x2="180" y2="264"/><polygon class="ah" points="175.1,255.6 184.9,255.6 180,264"/><rect class="card" x="12" y="264" width="336" height="56"/><text class="b" x="180" y="288" text-anchor="middle">Nereid thetis</text><text class="s" x="180" y="308" text-anchor="middle">(the installer)</text><line class="ln" x1="180" y1="320" x2="180" y2="344"/><polygon class="ah" points="175.1,335.6 184.9,335.6 180,344"/><rect class="card" x="12" y="344" width="336" height="172"/><text class="h2" x="28" y="370" text-anchor="start">Installed</text><rect class="col" x="28" y="384" width="304" height="36"/><text class="s" x="180" y="407" text-anchor="middle">Reefs</text><rect class="col" x="28" y="426" width="304" height="36"/><text class="s" x="180" y="449" text-anchor="middle">Nereids</text><rect class="col" x="28" y="468" width="304" height="36"/><text class="s" x="180" y="491" text-anchor="middle">Mandates</text><rect class="actor" x="0" y="562" width="360" height="58"/><text class="b" x="180" y="587" text-anchor="middle">nereus reef apply</text><text class="s" x="180" y="607" text-anchor="middle">(and nereid apply, one at a time)</text><line class="ln" x1="180" y1="562" x2="180" y2="518"/><polygon class="ah" points="175.1,526.4 184.9,526.4 180,518"/></svg>
</figure>
<!-- diagram:runtime:end -->

*Init lays down core; a profile, or a person one command at a time, adds the rest.*

## How it works

- [`nereus init`](../specs/cli/core.html#init) installs the kinds, the namespace, the Nereus API, core and the tenancy Reef with Helm; the profile `core`, the default, installs nothing more.
- [`nereus init --profile internal-developer-platform`](../specs/cli/core.html#init-profile) adds a profile: the Nereid `thetis` installs its Reefs, Nereids and Mandates, and `init` waits until they are Ready.
- A profile never writes the order: each Nereid comes after the Nereids of the Reefs it requires, read from its image's label `core.getnereus.dev/requires`.
- A profile adds nothing the commands cannot do: `nereus reef apply`, `nereus nereid apply` and `nereus mandate create` do the same by hand, on a running installation.
- A profile never carries a secret: credentials reach a Nereid through the secrets Reef, encrypted on the client, once the profile is installed.

## Not this

- Not a fixed install: Reefs and Nereids come and go on a running installation, and init never has to run again for them.
- Not a size: profiles are named by purpose, never `minimal` or `full`; `core` alone is the default, so a plain init stays fast.
- Not access: who may do what is a role, in [Tenancy and access](tenancy-and-access.md).

## Next

[Undercloud and overcloud](undercloud-overcloud.md): where an installation starts when its home is a cloud.
