# 0010. Build trigger: a new commit on a Mirror builds a Workload

**Status:** Proposed (2026-11-11)

From #914 (a push starts a build), with the owner's decisions of 2026-11-11 recorded on the issue.

## The answer

A `Trigger` of the build Reef names a Workload (here `triton`, the Workload of `catalog/workloads/triton.yaml`, whose source is this repository). Its Nereid follows the scm Reef's Mirror of that Workload's repository and, whenever the Mirror's `status.commit` changes, creates a Build of that commit. Each Nereid writes only its own Reef's objects: the forgejo Nereid keeps the Mirror's commit, the buildkit Nereid creates the Builds.

```console
$ nereus scm mirror create nereus --from https://github.com/getnereus/nereus
✓ scm/mirrors/nereus created (mandate forgejo)

$ nereus build trigger create triton --workload triton
build/triggers/triton created (mandate: buildkit, nereid: buildkit)

Next steps:

  nereus build trigger get triton

$ git push origin main      # the Mirror pulls it on its interval

$ nereus build trigger list
TRIGGER  WORKLOAD  MIRROR  COMMIT   LAST BUILD      STATUS
triton   triton    nereus  a1b2c3d  triton-a1b2c3d  Ready

$ nereus build list
BUILD           WORKLOAD  COMMIT   STATUS     DIGEST
triton-a1b2c3d  triton    a1b2c3d  Succeeded  sha256:4f2a…
```

## Decided (owner, 2026-11-11)

- **The build Reef turns a commit into a Build**, not the scm Reef's webhook receiver: no Nereid writes another Reef's objects.
- **Webhook or watching is the Mirror's choice.** The forgejo Nereid already reads each Mirror's head on every pass (15 s), which is the watching mode; Forgejo's webhook, which shortens that by at most one pass, is a later slice (`nereus scm mirror create --webhook`). The build side is the same for both.
- **The opt-in is a kind of the build Reef, `Trigger`**, not a field of the Workload: the catalog Reef stays as it is, and deleting the Trigger stops it.
- **A new Trigger builds the commit the Mirror holds now**, without waiting for the next one: its list shows a result at once.
- **A burst of pushes builds the last commit only:** while a Build of the Trigger is not over (no phase yet, `Pending` or `Running`), nothing new starts, which bounds the builds, as spec 0009 asks.
- **Deleting a Trigger keeps its Builds:** a Build is an image in the registry; the Trigger only automates them.

## The `Trigger` kind

Cluster-scoped, as a Build, a Workload and a Mirror are (`reefs/build/triggers.yaml`).

- `spec.workload` (required, never changes): the Workload of the catalog Reef it builds.
- `spec.owner` (an Organization or a Project): the owner of every Build it creates; absent, the Builds have none, as a Build created by hand.
- `spec.mandate`: a build Mandate, so the Nereid that serves it and builds; absent, the Reef's default.
- `status`: `nereid`, `mirror` (the Mirror it follows), `branch`, `commit` (the last commit it saw on the Mirror), `lastBuild` (the Build it created last) and the `Ready` condition.

## What the Nereid does on each pass

1. Reads the Workload. None: `NoWorkload`. A Workload with no `spec.source.repository`: `NoSource`.
2. Finds the Mirror whose `spec.from` is that repository (same host, owner and name, any case, with or without `.git`). None: `NoMirror`. More than one: the oldest, as the forgejo Nereid does.
3. The Mirror is not `Ready`: `MirrorNotReady`. The Workload names a branch other than the Mirror's `status.branch`: `OtherBranch` (a Mirror follows its default branch only).
4. The Build it made last is `Pending` or `Running`: nothing new (`Building`); intermediate commits are skipped, so a burst of pushes builds the last one.
5. Otherwise, when no Build of the Mirror's commit exists for this Trigger, it creates `<trigger>-<first 7 digits of the commit>` (the Trigger's name cut to 55 characters), with the Workload, the full commit, the Trigger's owner and Mandate, and the label `build.getnereus.dev/trigger: <trigger>`. A Build of that name that is not this Trigger's: `NameTaken`. Then `Ready`, with `commit` and `lastBuild`.

The details of those steps:

- A Build with no phase yet counts as not over, as `Pending` does (step 4).
- `status.commit` is the Mirror's commit the Trigger saw on its last pass, built or not yet.
- The cut name loses a trailing hyphen before `-<commit>`, so it never holds `--`.
- The Build carries the Trigger's `spec.mandate` only when it names one; with none, the Build names none either and gets the Reef's default, as a Build created by hand.

A new Trigger builds the commit the Mirror holds when it is created. A Build it created is never deleted by it: deleting the Trigger leaves its Builds.

## Security (OWASP)

- **A08, software and data integrity:** only the commits a Mirror pulled are built, from the repository the Workload names; nothing outside the cluster can name a commit. The Forgejo webhook slice adds its signature check before it changes anything.
- **A01, broken access control:** a Trigger's Builds carry its owner, so the gates of spec 0009 hold: in portable mode only an operator's Builds run, a team's ends `SandboxRequired`. A Trigger cannot give its Builds an owner the person could not give a Build by hand (the CLI checks it as for `nereus build create`).
- **CI/CD-SEC-04, poisoned pipeline execution:** a Mirror pulls a branch, never a fork's pull request.
- **Bounded builds:** at most one Build of a Trigger runs at a time (step 4).

## Stand-ins

None: the trigger watches the Mirror's status; the webhook is a later slice, not a stand-in.

## Done when

- `make test`: the buildkit Nereid's unit tests cover each step above; the CLI's cover `nereus build trigger create|list|get|delete`.
- `make scene-build` (owner, 2026-11-12): a Build fetches its Workload's repository from upstream, and its fetch never reaches a private address (#1141), so a fake Git host in the cluster cannot end in `Succeeded`. The scene has two acts instead. First, a public repository: a Mirror `build-fixtures` of `getnereus/build-fixtures` on GitHub, a Workload `fixtures` of its `main` and the Trigger `fixtures`, which builds the Mirror's commit at once, `Succeeded` with the registry's digest; this repository and its Workload `triton` take their place once it is public (#1337), since a Mirror of a private repository needs a credential (#1396). Second, a push: a Mirror `app` of the fake Git host and a Trigger `app`; a commit on the fake reaches the Mirror within a pass and makes a Build of that commit, whose fetch fails since the host is private. The rule of a burst of pushes (one Build at a time, the last commit) stays in the unit tests, since the fake's fetch fails in seconds.

## What is left to other issues

- Forgejo's webhook (`--webhook` on a Mirror), which updates the Mirror's commit at once.
- A branch other than the Mirror's default branch.
- A quota per repository across Triggers.

## Learn more

- OWASP, [Top 10 CI/CD Security Risks, CICD-SEC-04](https://owasp.github.io/www-project-top-10-ci-cd-security-risks/CICD-SEC-04-Poisoned-Pipeline-Execution).
- Flux, [image automation](https://fluxcd.io/flux/components/image/): a controller that follows a source and acts on a new revision, the shape a Trigger takes here.
