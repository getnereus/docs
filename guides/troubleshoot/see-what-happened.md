# See what happened

Find why a reef, a Nereid or an object is not `Ready`, starting from the CLI and going down to the object's events and the Nereid's log.

## Before you start

- A cluster from [Prepare the cluster](../../start/init.md), and `kubectl` for the last two steps.

## Steps

### 1. See which reef has a problem

[`nereus status`](../../specs/cli/core.html#status) gives one row per reef and its Nereid:

```bash
nereus status
```

``` { .text .output title="output" }
REEF            NEREID    VERSION  STATUS         AGE
authentication  keycloak  0.1.0    Ready          2m
core            built-in  0.1.0    Ready          4m
release         flux      0.1.0    Ready          3m
secrets         openbao   0.1.0    Ready          4m
tenancy         -         -        Ready          4m

Registry  localhost:5111
```

### 2. Look at the Nereid

[`nereus nereid get`](../../specs/cli/core.html#nereid-get) shows its image, digest and Mandates; a Nereid that is not `Ready` also says why (`Unavailable`, `NotConformant`).

```bash
nereus nereid get keycloak
```

``` { .text .output title="output" }
Name:         keycloak
Reefs:        authentication
Image:        localhost:5111/keycloak-controller:0.1.0
Digest:       sha256:0f4675ab231b4e6d4a439d0c7d8e5b07011f35802b38592851542cf56666be93
Title:        authentication-keycloak-controller
Description:  The keycloak Nereid of Nereus, for the authentication reef
Status:       Ready
Mandates:     keycloak (default)
Age:          2m
```

### 3. Read the object's events

Each object's `Ready` condition says why in its `message`, and every change of a step is a Kubernetes Event on the object, kept when the Nereid restarts: `kubectl describe` shows them, under Events.

### 4. Read the Nereid's log

A Nereid logs JSON Lines, one per reconcile pass and its reason: `kubectl logs deployment/keycloak --namespace nereus-system`.

## Check it worked

[`nereus doctor`](../../specs/cli/core.html#doctor) runs ten checks of the installation, pass or fail, and says the next step for one that fails:

```bash
nereus doctor
```

## Next

- [When the Nereid stops](nereid-stops.md): `Unavailable`, and how the commands come back.
- [Pass the conformance tests](../build/conformance.md): the status every object must carry.

## Learn more

- [Spec 0003](../../specs/0003-nereid-conformance.md): the `Ready` condition, the steps and their events.
