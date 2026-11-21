# 0001. First slice: init, Nereid list, and a fake Nereid that publishes commands

**Status:** Done (2026-10-17)

Its commands and kind follow ADR 0011 since #98: the `controller` commands live under `system`, and the `Controller` kind is named `Nereid` (`Implementation` in the current code, to be renamed).

## Intent

Prove the two ideas the project rests on, end to end, with the least code: `init` only prepares a cluster (ADR 0003), and an installed Nereid adds its own commands to the CLI (ADR 0004). Nothing real is installed: the first Nereid is a fake whose commands only simulate their output.

## The scene that ends the slice

```bash
nereus init --target k3d --create-cluster --name platform-local   # creates the k3d cluster, sets the kube context
nereus nereid list                                 # empty
nereus nereid apply fake \
  --reef release \
  --image <registry>/fake-controller:0.1.0
nereus nereid list
# NAME  STATUS
# fake  Ready
nereus fake --help                                                # shows the commands the fake Nereid published
nereus fake repo add example https://charts.example.com
nereus fake repo list
# NAME     URL
# example  https://charts.example.com
nereus nereid delete fake
nereus fake --help                                                # gone
```

The project is `platform-api` (`github.com/getnereus/nereus`) and the CLI binary is `nereus`. Keep the binary name in one place, so a later rename is a one-line change.

## Parts

1. **`init`**
   - `--target k3d --create-cluster --name <name>`: creates a k3d cluster (fails with a clear message when `k3d` or `docker` is missing), points the kube context at it, applies the project's CRDs (the `Nereid` kind), and records the cluster and context in the CLI config.
   - Running it again reuses the existing cluster.
   - Without `--create-cluster`, it uses the cluster of the current kube context.
2. **The `Nereid` CRD**
   - `spec`: `image`, written by the CLI.
   - `status`: `conditions` (`Ready`) and `commands`, the command description of ADR 0004, written by the Nereid (ADR 0005).
3. **`nereid list | apply | delete`**
   - Until the Platform API exists, the CLI talks to the cluster with the kubeconfig.
   - `apply` creates the `Nereid` object and a Deployment plus Service running the image.
   - `delete` deletes all three.
4. **Dynamic commands**
   - The CLI caches each Nereid's `status.commands` (refreshed by `nereid list` and `nereid apply`), builds a command group named after the Nereid, and sends each run to its Nereid through the Kubernetes API Service proxy. It prints what comes back.
5. **The fake Nereid image**
   - Follows the `runner` pattern: an `entrypoint` that sets `umask 0002` and runs the requested command, with a work directory on a volume (an `emptyDir` is enough for this slice).
   - It serves a tiny HTTP endpoint that runs its scripts.
   - On start, it writes its `status.commands` and `Ready`.
   - `repo add` appends to a file in the work directory, and `repo list` reads it.

## Constraints

- Every rule in `CLAUDE.md` and `docs/adr/` applies, especially "public by design" (ADR 0007) and "one writer per field" (ADR 0005).
- Walking skeleton first: the scene above working once beats any part done well on its own.

## Decisions

1. **The CLI's language:** Python with `uv` and `typer` (ADR 0008).
2. **The API group** of the CRDs: `platform.wasp.silvios.me` (current code, to be renamed `core.getnereus.dev`), for the proof of concept (ADR 0009).

## Learn more

- **Walking skeleton** (Alistair Cockburn; [WalkingSkeleton on the C2 wiki](https://wiki.c2.com/?WalkingSkeleton)): "a tiny implementation of the system that performs a small end-to-end function"; the scene of this slice is one.
