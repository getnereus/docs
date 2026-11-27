# 0002. Reef at runtime: a Reef added from the CLI, and the reference Nereid installed into it from its image label

**Status:** Done (2026-10-17)

## Intent

Prove ADR 0010 end to end from the CLI with the least new code, the way the first slice proved ADRs 0003 and 0004: a Reef is an object added at runtime, a Nereid is installed into the Reef its image declares, and the command group is named after the Reef, not the Nereid (ADR 0011). It is the second cut of #45 (#99), after the `system` group of #98, and the first part of layer 1 of [spec 0003](0003-nereid-conformance.md): the `reef` label, read from the registry.

## The scene that ends the slice

```bash
nereus init --yes                                   # also creates the local registry localhost:5111
make reference                                             # builds the reference image with its label, pushes it there
nereus reef apply release --from-file ./reefs/release/
nereus reef list
# NAME     NEREID
# release  -
nereus nereid apply reference-release \
  --reef release \
  --image localhost:5111/reference-release-controller:0.1.0
nereus release --help                               # the group is named after the reef
nereus release repo add example https://charts.example.com
nereus release repo list
nereus nereid list
# NEREID             REEFS    IMAGE                                              STATUS  AGE
# reference-release  release  localhost:5111/reference-release-controller:0.1.0  Ready   5s
nereus nereid delete reference-release
nereus release --help                               # the reef stays: no Nereid installed
nereus reef delete release
```

`test/scene` runs it on a throwaway k3d cluster, and also checks the two refusals: installing before the Reef was added, and an image with no Reef label.

## Parts

1. **The `Reef` kind** (CRD, cluster-scoped): only a name for now. `spec.active` comes with #72; the contract of a Reef with #18. Written by the CLI (ADR 0005).
2. **The Reefs on the `Nereid` kind**, `spec.reefs`, required, written by the CLI.
3. **`nereus reef apply | list | delete`.**
   - `apply` refuses a name that is not a command name or that a command of the CLI already uses (`init`, `system`), and is idempotent.
   - `list` shows each Reef with the Nereid installed into it.
   - `delete` is refused while a Nereid of the Reef is installed, naming the `nereus nereid delete` to run.
4. **`nereus nereid apply <name> --image <ref> [--reef <reef>]`** follows steps 1, 3 and 4 of spec 0003's layer 1, with its messages:
   - It reads the label `<API_GROUP>/reef` (`cli/src/nereus/names.py`) from the registry. Its value is a comma-separated list.
   - With `--reef`, it uses that Reef, which must be one the label lists when there is a label.
   - With no `--reef`, it uses the one name the label lists; it refuses several names or none.
   - It refuses a Reef that was not added (`nereus reef apply <name> --from-file ./reefs/<name>/`).
5. **The registry client** (`cli/src/nereus/registry.py`), standard library only, behind one function, `labels(image, platform)`:
   - References are read as Docker reads them (`reference-release-controller` is `docker.io/library/reference-release-controller`).
   - `GET /v2/<name>/manifests/<ref>`; for an index, the manifest of the platform of the cluster's first node (attestation entries have none and are skipped); then `GET /v2/<name>/blobs/<config digest>` and its `.config.Labels`.
   - A `401` with a `Bearer` challenge gets an anonymous token from its realm, scoped to `repository:<name>:pull`.
   - HTTPS, except for `localhost`, `*.localhost` and loopback addresses, as Docker does.
6. **Command groups named after the Reef** (ADR 0004, ADR 0010). The cache holds one entry per Reef with its Nereid and the commands it published. A group with no Nereid says so, with the install hint. The first slice's group named after the Nereid is gone.
7. **The local registry.** `nereus init --create-cluster` on k3d creates the registry `k3d-nereus-registry.localhost` on port 5111 of the loopback (`names.REGISTRY`, `names.REGISTRY_BIND`, `names.REGISTRY_PORT`; #654: it has no authentication, so nothing on the local network reaches it), or reuses it. It creates the cluster with `--registry-use`, and with a mirror of `localhost:5111` to that registry, so one reference serves `docker push` on the machine, the CLI's read and the cluster's pull. One registry serves every cluster `init` creates. Docker pushes over plain HTTP to `localhost:<port>`, but not to `k3d-*.localhost:<port>`, so the mirror is needed.
8. **The reference image** gets `LABEL ${API_GROUP}/reef=${REEF}`. `API_GROUP` is a build argument with no default, passed from `names.py` by `make reference` and `test/scene`, so a rename stays a one-line change. `REEF` defaults to `release`; empty, it builds an image that declares no Reef, for the scene's refusal.

## Decisions

1. **One Nereid per Reef until #72.** Installing a second one into a Reef was refused, naming the one to uninstall: before `spec.active` existed, nothing said which one the group's commands would go to. Superseded (owner, 2026-11-19, #1894): a Reef takes several Nereids, one the default and the others reached through a Mandate (ADR 0011).
2. **`nereus init` creates and owns the local registry**, shared by every cluster it creates, on a fixed port so the reference reads the same in the docs and on every machine. A cluster reused by `init` keeps the registries it was created with.
3. **The platform of an index** is the first node's. Mixed-architecture clusters wait for a need.
4. **The labels the image declares beyond `reef`** (`requires`, `nereid`, the version) are spec 0003's, not this slice's.

## Security and quality attributes

Under the lens of #28, this slice is **alpha**: a proof that works end to end on a throwaway cluster, never production.

- **Read before run.** The Reef is read from the registry before anything is pulled or run, two or three small requests and no layer, so a wrong image is refused before it reaches the cluster.
- **What the CLI trusts from a registry.**
  - References are validated before they become a URL.
  - A manifest fetched by digest, and the config blob, are checked against their digest.
  - Responses are capped at 4 MiB.
  - Redirects are followed by hand: the token is dropped when the host changes, and HTTPS never falls back to HTTP.
  - Label values are checked as command names before they name a group.
- **The digest gap, closed by #126.** The labels were read from a tag, and the cluster pulled the same tag: a tag pushed again between the read and the pull ran an image whose labels were never read. The install now resolves the tag to the digest of the manifest it read and records `spec.image` as `<repository>@sha256:...` (spec 0003, Good Citizen rule 3), so the cluster pulls what was read. Signature verification comes later (#126).
- **Anonymous only.** A registry that asks for credentials is refused with a message that points to #87. Private registries and their credentials are #87.
- **Plain HTTP only for this machine's registry**, the local one `init` creates.
- **What beta would need:**
  - two Nereids of one Reef, with one active (#72), instead of refusing the second;
  - private registries (#87);
  - the rest of spec 0003's layer 1: `requires` checked, the Nereid's name and version from its labels.
- **Fitness functions:**
  - unit tests of the registry client against a local HTTP registry: a plain manifest, an index, a missing label, the bearer challenge, a refused `401`, a config that does not match its digest;
  - unit tests of every refusal;
  - `test/scene` end to end.

## Constraints

Every rule in `CLAUDE.md` and `docs/adr/` applies, especially "one writer per field" (ADR 0005) and "the API never names a Nereid": the CLI reads the Reef from the image, never from a list of known Nereids.

## Learn more

- **Fitness functions** come from *Building Evolutionary Architectures* (Neal Ford, Rebecca Parsons, Patrick Kua, O'Reilly, 2017; [evolutionaryarchitecture.com](https://evolutionaryarchitecture.com/)): an automated check that a quality of the architecture holds, run on every change. This spec lists its own under "Security and quality attributes".
- **OCI image annotations** ([opencontainers/image-spec](https://github.com/opencontainers/image-spec/blob/main/annotations.md)): the standard keys an image's labels use (spec 0003).
