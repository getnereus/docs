# 0014. Profiles: core is only the engine, and a profile lists the Reefs, Nereids and Mandates to install

!!! note "In short"
    Core is only the engine; a profile lists the Reefs, Nereids and Mandates to install, run as the commands a person would type. It revises what `nereus init` installs (ADR 0003). Status: Proposed (2026-10-26).

**Status:** Proposed (2026-10-26)

## Context

Today `nereus init` installs the `core` kinds and, with them, the `secrets` Reef, the `openbao` Nereid, the default `vault` Mandate and the Mandate's key (ADR 0003 (init prepares core and secrets; Reefs and Nereids come at runtime), #404, #406). Every other Reef comes later, one command at a time: `nereus reef apply`, `nereus nereid apply`, `nereus mandate create` (ADR 0011, #409). A person who wants a working platform has to know which Reefs, Nereids and Mandates to apply, and in which order.

Two things are mixed in `init` today. One is the engine: the kinds that let Reefs, Nereids and Mandates exist at all. The other is a choice of capabilities, the secrets Reef, made for the platform Nereus is built for first. Nereus is meant as a generic engine, and the Internal Developer Platform is one use of it.

## Decision

**Core is only the engine.** The `core` Reef is the `Reef`, `Nereid`, `Mandate` and `Profile` kinds of `core.getnereus.dev/v1alpha1`, plus the `User` of ADR 0006 (the person belongs to core, not to an authentication Nereid), and nothing else. Core installs no other Reef: the `secrets` Reef, the `openbao` Nereid and the `vault` Mandate move into a profile. This revises what `nereus init` does since #406 (ADR 0003); the change is planned here and made in its own issue.

**A profile is a list of what to install:** Reefs, Nereids and Mandates. It runs as the commands a person would type, `nereus reef apply`, `nereus nereid apply` and `nereus mandate create` (ADR 0013), so a profile adds nothing the commands cannot do. The install order is not written in the profile: it comes from each Nereid's requirements (`spec.requires`, from the image's label `core.getnereus.dev/requires`). For example, keycloak requires the vault, so the vault comes first.

```bash
# Core only, the default: to build piece by piece
nereus init

# The Internal Developer Platform: secrets, authentication, authorization, policy and environments
nereus init --profile internal-developer-platform
```

```yaml
# A sketch of the profile; its exact fields belong to the issue that builds it.
apiVersion: core.getnereus.dev/v1alpha1
kind: Profile
metadata:
  name: internal-developer-platform
spec:
  reefs: [secrets, release, authentication, authorization, policy, environment]
  nereids:
    - {name: openbao, reefs: [secrets]}
    - {name: flux, reefs: [release]}
    - {name: keycloak, reefs: [authentication]}
    - {name: openfga, reefs: [authorization]}
    - {name: kyverno, reefs: [policy]}
    - {name: vcluster, reefs: [environment]}
  mandates:
    - {name: vault, reef: secrets, nereid: openbao, default: true}
    - {name: flux, reef: release, nereid: flux, default: true}
```

**Profiles are named by purpose, never by size.** There are two:

| Profile | What it installs |
|---|---|
| `core` | core only, nothing else, the default: for building piece by piece |
| `internal-developer-platform` | the first full profile: Nereus as an Internal Developer Platform with interchangeable pieces. The `secrets` Reef with `openbao` and the `vault` Mandate, `release` with `flux` and the `flux` Mandate, `authentication` with `keycloak` (Keycloak itself a Release of `release`), `authorization` with `openfga`, `policy` with `kyverno`, and `environment` with `vcluster` (open source, a virtual cluster on the local k3d) |

- The name `internal-developer-platform` is written in full on purpose: "IDP" is often read as Internal Developer Portal. The docs use no short name and no alias.
- There is no `minimal`, `default`, `empty` or `full`: the profile of core alone is named after what it installs, `core` (it was `empty` until order 20261026-0640).

**Nereus is a generic engine, and the Internal Developer Platform is its first distribution:** a profile. Other domains may come as other profiles on the same engine.

**A profile never carries a secret.** Credentials reach a Nereid through the `secrets` Reef after the profile is installed (`nereus secrets apply`, encrypted on the client, ADR 0011), never through the profile.

**`nereus init` with no `--profile` installs `core`, core alone** (#424). The full platform comes only when asked for, with `--profile internal-developer-platform`. A plain `init` stays fast and installs nothing a person did not ask for; the trade-off is one more flag to see something working. This reverses the first decision (order 20261026-0006), which made `internal-developer-platform` the default.

**The name is "Profile"**, with no word from the sea: it says what it is to a person who meets it for the first time.

### Origin

All decided by the owner: on 2026-10-25 (order 20261025-2359, which supersedes order 20261025-2352) and on 2026-10-26 (orders 20261026-0003, 20261026-0006, 20261026-0035 for the `environment` Reef, and 20261026-0640 for the default `core` and the decisions below).

Decided on 2026-10-26 (order 20261026-0640), on the open points of order 20261026-0508:

- **The stand-in stays:** keycloak's requirements on the `secrets` and `release` Reefs are written in the CLI's table of the local Nereids until each local Nereid has its own image label.
- **A cloud target refuses `--profile`** and installs Azure Key Vault as its secrets Nereid; accepted until the issue that joins profiles and targets.
- **#414 (the secrets Reef missing after `nereus init` in one CI run) stays open** until its cause is found, with no rush.
- **Core holds the `User` kind** (ADR 0006): confirmed.
- **Every ADR stays `Proposed`** until the profile `internal-developer-platform` runs complete, with its five Reefs. The orders are in Drive `#pontos/beach/`.

## Prior art

- **Istio installation profiles** ([istio.io, "Installation Configuration Profiles"](https://istio.io/latest/docs/setup/additional-setup/config-profiles/)): `istioctl install --set profile=<name>` picks a set of components. `default`, `demo`, `minimal`, `remote`, `empty`, `preview` and `ambient` are mostly named by size or stage. Nereus takes the `empty` base and the idea of one command that installs a known set, and names its profiles by purpose instead.
- **Debian tasksel** ([wiki.debian.org/tasksel](https://wiki.debian.org/tasksel)): during installation, a person picks a task ("web server", a desktop), and tasksel installs the packages for it. A Nereus profile is the same shape: a task named by purpose, made of pieces that also install one by one.
- **Helm umbrella charts** ([helm.sh, "Complex Charts with Many Dependencies"](https://helm.sh/docs/howto/charts_tips_and_tricks/#complex-charts-with-many-dependencies)): one chart that lists its subcharts as dependencies. A profile differs in two ways: it lists pieces that each keep their own commands, and it leaves the order to the Nereids' requirements.

## Consequences

- **`nereus init`** installs core, then the profile through the same code paths as `nereus reef apply`, `nereus nereid apply` and `nereus mandate create`. Built in #420: `--profile empty` (now `core`, the default since #424) and `--profile internal-developer-platform`, whose `keycloak` Nereid requires the `secrets` Reef, so the secrets Reef comes as that requirement (order 20261026-0508); ADR 0003 is rewritten with it. The profiles are a table in the CLI (`cli/src/nereus/profiles.py`) until the `Profile` kind exists.
- **`--target azure`** (ADR 0003) still decides the first secrets Nereid (Azure Key Vault). The issue that builds `--profile` settles how the profile's `secrets` entry follows the target.
- **The `policy` Reef and the `kyverno` Nereid do not exist yet.** The profile installs the other Reefs of its list: `authorization` with `openfga` and its default Mandate `openfga` (#1655, spec 0011), which turns the check on in the Nereus API, and `environment` with `vcluster`. The `teams` Reef, which no Nereid serves, is applied by a lane of its own before `openfga`, which reads its Teams and Members. The `environment` Reef is the first PoC's `environment` API group (an environment was a virtual cluster); an `azure-aks` Nereid may come later as its interchangeable alternative, decided when the first real environments are provisioned.
- **The order comes from the Nereids.** A Nereid's image declares what it requires (`core.getnereus.dev/requires`): keycloak's must name the `secrets` Reef for the vault to come first. Every local Nereid's Dockerfile declares it since #1368, which retired the `requires` column of the CLI's table that stood in for it.
- **The default `init` stays fast,** since it installs core alone; the time SLO of `init` (spec 0004) is checked in CI on that path, and the profile's own time shows in `nereus profile apply`.
- **`nereus profile apply <name>` layers a profile on core** (#425), idempotent as `kubectl apply`: the demo is `nereus init`, then `nereus profile apply internal-developer-platform`, and `nereus init --profile <name>` is the shortcut for both. `nereus profile list` and `nereus profile describe <name>` show the built-in profiles; `nereus profile create` (custom profiles) is parked.
- **The profile is a setting of `init`** (#426): `spec.profile` in `init.yaml`, besides `--profile`; the flag wins over the file.
- **The `Profile` kind joins core** (ADR 0009). First the CLI ships the profiles and runs them. Later the applied Profile becomes an object in the cluster.
- **Later, better than good enough:**
  - The Profile is applied as a resource in the cluster, and `nereus status` shows the drift between what the profile asks for and what runs. The PoC's hand-written "Divergences" list becomes a CI check.
  - An engine-boundary test proves that a Reef outside the platform domain can be added without touching core.

## Amendment (2026-10-30): the tenancy Reef counts as part of core

**Every `nereus init` applies the `tenancy` Reef**, the default `core` profile included, and a cloud target too (#646, #651). This does not change the decision above: core is still only the engine, and a profile still lists the Reefs, Nereids and Mandates a person chooses. The tenancy Reef counts as part of core, not as a choice of a profile, for three reasons:

- **The API keeps the tree, as it keeps the core kinds** (ADR 0015, tenancy: a tenancy Reef whose kinds come from each instance, with one fixed shape): the Reef has no Nereid, no Mandate and no secret, so applying it installs no capability a person did not ask for.
- **Whatever says whose a thing is points to it:** the catalog, an Environment, a resource Instance and a Mandate's `match` name an `owner` in the tenancy group, so every installation needs the tree before its first Reef with an owner.
- **It is still a Reef, not more kinds in `core.getnereus.dev`:** each instance applies its own kinds from its `reefs/tenancy/`, and a tenancy Nereid may come later to sync the tree with another system; ADR 0015 says why tenancy is not in `core`.

So "core installs no other Reef" reads: no other Reef that a Nereid looks after. `nereus status` shows the tenancy Reef `Ready` with no Nereid (#651), and `nereus profile describe` names it under every profile.

*Origin: the open points of #646 (the tenancy Reef's CRDs and admission), recorded in #651 by an agent on 2026-10-30; pending the owner's review, as the whole ADR.*

*Proposed 2026-10-26 from orders 20261025-2359, 20261026-0003 and 20261026-0006; the `environment` Reef added from order 20261026-0035; the default `core` from order 20261026-0640; keycloak requires the `release` Reef, which releases Keycloak, from order 20261026-0840 (step 2). Raw data in Drive `#pontos/beach/`. Amended 2026-10-30 from #651: the tenancy Reef counts as part of core.*

## Amendment (2026-11-05): the order lives in thetis, the installer Nereid

**A profile installed from the chart `nereus` runs in the cluster, in thetis' reconcile** (#1053, parent #1049). The chart's value `profile` writes the `Profile` named `nereus` (`spec.profile`), and thetis, a Nereid that comes up with core, runs the profile's steps: the same `profiles.steps` that `nereus init --profile` runs, from the CLI's own package in its image. The order still comes from each Nereid's requirements, never from the profile. It now lives in that reconcile, not in `init` and not in Helm hooks.

- **Why a Nereid:** each Nereid's step resolves its image by digest for the nodes' platform, reads the image's labels, creates its Secrets, and waits for it to report Ready. Helm cannot do that at run time, and its hooks order only the creation of objects and stay out of the release.
- **The status shows each step** (`Done`, `Waiting` with why, `Pending`) and a `Ready` condition; a Nereid whose required Reef has no Ready Nereid waits and names it.
- **thetis' rights are wide:** it writes CRDs, admission policies, Deployments, Secrets and each Nereid's RBAC, so its ClusterRole holds `bind` and `escalate`.
- **The `Profile` is the embryo of the Operator of #77** (the `Platform` resource): one description of the platform, kept reconciled after the install.
- **The first profile thetis installs is `secrets`**, the secrets Reef with openbao alone; #1054 brings `internal-developer-platform`.
- **`nereus init --profile` runs no step of the profile** (#1055): it passes the profile to the chart `nereus` as a value, then waits for the profile's Nereids and the `Profile` to be Ready, printing each Nereid's time. `nereus profile apply` still runs the same steps from a laptop.

*Origin: decided by the owner on 2026-11-05, in #1049 and #1053.*

## Amendment (2026-11-08): the Profile wins

**thetis keeps a Profile's Nereids installed, so a Nereid leaves the platform through the Profile, never by a delete by hand** (#1231, from #1056). thetis runs the Profile's steps every 30 s and puts back a Nereid of the profile deleted by hand; that stays, as with Flux.

- **`spec.exclude`** lists the Nereids of the profile a person left out: thetis does not install them and deletes them, the last installed first, as `nereus nereid delete` does. Leaving out a Nereid that a kept one requires is refused, naming it.
- **`nereus profile apply <profile> --without <nereid>`** writes that list, repeated for each Nereid; the list given replaces the one the Profile holds, as `apply` does. It waits until thetis reconciled it. The profile itself stays the chart's value.
- **`nereus nereid delete`** refuses a Nereid the Profile holds, `--force` or not, naming the Profile and the `profile apply` line that leaves it out.

*Origin: decided by the owner on 2026-11-08, in #1231.*

## Amendment (2026-11-11): a profile is one YAML file the chart renders into the Profile's spec

**Status of this amendment:** Proposed.

**A profile is one YAML file, keyed by Reef, that the chart `nereus` ships and renders into the spec of the single `Profile` named `nereus`; thetis installs what that spec describes** (#1363). It replaces the sketch of the Decision above, which named openfga and kyverno, which no profile installs:

```yaml
profile: secrets
reefs:
  - name: secrets
    nereids:
      - name: openbao
        # Optional: with none, <registry>/<nereid>-controller:<chart version>, the convention (#1364).
        image: {repository: ghcr.io/getnereus/nereus/openbao-controller, tag: 0.1.0, digest: "sha256:..."}
    mandates:
      - {name: default, nereid: openbao, default: true}
```

- **The files live at `cli/src/nereus/charts/nereus/profiles/<name>.yaml`**, outside `templates/`. The chart renders the one its value `profile` names under `spec:` with `.Files.Get`, and fails on a name with no file. There is still one `Profile`, named `nereus`, and `spec.profile` stays the name; `spec.exclude` is unchanged.
- **A Nereid serving a second Reef is repeated there by name, without its image.** A Mandate's `params` are never secret, as the Decision says of a profile.
- **thetis reconciles the object's spec**, what this installation asked for; the CLI (`profile apply`, `describe`, `list`, `init`) reads the files. One parser, `profiles.py`: `load(name)` reads a file, `from_spec(spec)` reads an object, both into one dataclass that `steps()` takes.
- **`spec.reefs` is required** (#1370): thetis, `nereus status` and `nereus nereid delete` read the spec alone, never the file of its name; a spec with no `reefs` is refused (the CRD, and thetis in the `Profile`'s status).
- **One profile per installation:** profiles are alternatives, not layers; composing them waits for a marketplace.
- **The order is never in the file:** it comes from what each Nereid requires, its image's label `core.getnereus.dev/requires`, read from the registry; the label wins (#1368). With no registry answering (`nereus profile describe` or `--dry-run` with the network off), the offline list `cli/src/nereus/requires.yaml` stands in: `make chart` writes it from the labels of `controllers/*/Dockerfile`, and a test fails when a Dockerfile that names a Nereid lacks the label or when the list differs from the labels.
- **An image the profile pins runs as pinned;** the local registry (`NEREUS_NEREIDS_REGISTRY`, `NEREUS_NEREIDS_TAG`) rewrites its repository prefix and its tag, and drops its digest only when it names another registry or another tag than the pinned ones (#1403). A release pins tag and digest (#1369). *Replaced on 2026-11-12, below: nothing rewrites an image.*
- **Reef contract versions stay in `contracts.pinned`;** the ClusterRole stays generated by `make chart`.

**The steps:** the profile `secrets` first, as a walking skeleton, with `spec.reefs` optional and the other profiles falling back to their list in the CLI (#1365); `internal-developer-platform` and `core` as files, the entrance becoming `ingress` with its versions in the profile (#1366); Mandates from the file (#1367); the order from the image label (#1368); tag and digest pinned by a release (#1369); `spec.reefs` required (#1370).

**Prior art:** Istio's `manifests/profiles/*.yaml` (one file per profile, rendered by the installer), Flux's `OCIRepository.ref` (a tag for people, a digest for the machine), Crossplane's `Configuration` lock.

*Origin: decided by the owner on 2026-11-11, in #1363.*

## Amendment (2026-11-12): the Profile names every image, and thetis installs it as written

**The list of images is a parameter of what thetis is asked to install: the Profile** (#1425). The chart writes every Nereid's image into the `Profile`'s spec, and thetis installs each one as written: no convention and no registry override inside thetis.

- **The convention moves to the chart** (#1364): for a Nereid the profile file leaves without `image:`, the template writes the one the profile pins for it in another Reef, else `<nereids.registry>/<nereid>-controller:<nereids.tag>`; `nereids.tag` defaults to the chart's version. `profiles.filled` is the same rule in Python, and a test holds both equal.
- **Where the images come from is the installer's choice**, the chart's values `nereids.registry` (default `ghcr.io/getnereus/nereus`) and `nereids.tag`. The CLI's `init` passes the local registry, or the one `NEREUS_NEREIDS_REGISTRY` names, for a cluster that cannot reach the local one, such as Nereus inside an Environment.
- **thetis refuses a spec with a Nereid and no image** in the `Profile`'s status: that spec was not rendered by this chart. `NEREUS_NEREIDS_REGISTRY` and `NEREUS_NEREIDS_TAG` leave thetis' Deployment; `LOCAL_REGISTRY` stays, the local registry's address from a Pod, so thetis reads an image's labels there.
- This replaces the rewrite of #1363 and #1403: a pinned digest is never dropped, and a local build is named by the values the chart is given, not by thetis' environment.

*Origin: decided by the owner on 2026-11-12, in #1425, after #1406's recorded run found that thetis inside an Environment cannot reach the local registry.*
