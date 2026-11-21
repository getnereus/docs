# 0023. An external registry's push credential is the Repository's secret, read by the Nereid, never on the person's machine

!!! note "In short"
    An external registry's push credential is the Repository's `secretRef`, read by the Nereid through a SecretBinding, never on the person's machine. Status: Proposed.

**Status:** Proposed

## Context

#1229 (publishing goes through the platform) asks for `nereus release source publish`: a chart goes to an external OCI registry, `ghcr.io/getnereus` first, with no token on the person's machine, and the Source shows its digest. Until now, #850 (promote the seed images and the chart to ghcr.io/getnereus) copies by digest with `crane` and the owner's own token, on the owner's machine.

The pieces are there. The release reef's `Repository` already has a `secretRef`, a secret of the secrets reef. A `SecretBinding` turns a secret into a Kubernetes Secret in a namespace the vault allows. The registry reef (ADR 0021) already takes a person's upload with a ten-minute token of a push identity, through a port-forward, with crane in a container (#1010). Each Registry also has a read identity whose ten-minute tokens a Nereid may ask for (#1187).

## Decision

**An external registry's push credential is the target Repository's `secretRef`, read by the Nereid through a SecretBinding, never on the person's machine.**

- The secret holds one key, `config.json`, a docker configuration for the registry's host. The Nereid never opens it, so it does not care whose token is inside: a person's token today, a GitHub App's later (#1250, GitHub App token from the scm connection).
- The CLI packages the chart with `helm package` and builds its OCI artifact with Helm's media types. It uploads the artifact to a Registry of the cluster as `nereus registry repository publish` uploads an image, to the registry Repository `chart-<chart>`. Then it applies the Source with `spec.publish.from`, the upload by digest. The registry reef is required, and the command says so when it is missing.
- The Nereid of the Source's Mandate (`flux` today) asks a SecretBinding of the secret in its own namespace, for the copy alone, and deletes it once the copy is done. Before asking it, the Nereid checks that `spec.publish.from` names a Registry's own internal address, so a token never goes to another host.
- The copy is a Job of three crane containers, each with only its own credential: `pull` reads the upload with a ten-minute read token of the Registry, `push` writes it to the target at its version's tag, and `digest` reads the tag's digest back. The Nereid compares that digest with the uploaded one, as `scripts/registry/promote` does. On a match it writes `status.digest` and the Source is Ready (`Published`), otherwise `PublishFailed` with crane's last line.

## Prior art

- Flux's `HelmRepository.spec.secretRef` and `OCIRepository.spec.secretRef` name a docker configuration Secret the controller reads, never the user.
- `crane copy` (go-containerregistry) copies by digest, and Helm pushes charts as OCI artifacts with the media types used here (Helm 3.8+, `helm push`).
- GitHub Actions' `GITHUB_TOKEN` and the GitHub App tokens of #1250: a short-lived token held by the platform, not a personal one.

## Consequences

- No person ever holds the external registry's credential; whoever may write the secret in the vault decides who publishes. The credential sits in `nereus-system` only while a copy runs.
- The chart is pushed by tag, so Helm finds it by version, and checked by digest. A version uploaded before with another digest is refused, both in the cluster's Registry and at a target that forbids overwrites.
- The flux Nereid gains a Role on Jobs, their Secrets and their Pods' logs in `nereus-system`, plus a read token of a Registry's `read` ServiceAccount, held by an admission policy to `registry-*`, the Registry's own audience and ten minutes (the same policy the kubernetes Nereid has, #1187).
- The scene stands in for ghcr.io with a second Registry of the cluster, whose push token is the secret's content.
- #1250 replaces the personal token with a GitHub App token minted from the scm connection, with no change here: the secret's content changes, not who reads it.

*Origin: the owner's decisions of 2026-11-08 on #1229 (the CLI flow, the Source's fields, the credential, the copy Job and this ADR). Raw data in Drive `#pontos/raw/2026-11-08/`.*
