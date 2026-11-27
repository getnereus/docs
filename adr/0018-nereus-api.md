# 0018. The Nereus API is the one door: clients talk to it, and the Kubernetes API stays behind it

!!! note "In short"
    The Nereus API is the one door of the platform: clients talk to it with the person's token, and the Kubernetes API stays behind it. Status: Proposed (2026-10-30).

**Status:** Proposed (2026-10-30)

## Context

`docs/vision.md` and the slide `landscape` of the deck (`docs/presentations/nereus.yaml`) draw the Platform API as "the one door for every client: the CLI, a portal, an IDE reading an `app.yaml`, an agent", where "none of them needs a kubeconfig". `wasp-idp`, where the idea comes from, built it: the `platform` CLI called its Platform API (`GET /v1/me` for `platform whoami`), and the API validated the person's token and acted on the cluster.

Nereus has no such API yet. Every Reef is an API group served by the Kubernetes API (ADR 0002, ADR 0009), the CLI reaches it with the person's kubeconfig, and `nereus-mcp` runs on the person's machine and reads the cluster the same way, "until the Platform API exists". #54 (the first slice of the Platform API, after the CLI MVP) was closed as not planned on 2026-10-30.

The question came back with `nereus whoami` (#605): its first design sent the person's token to the Kubernetes apiserver (a `SelfSubjectReview`, the apiserver trusting the authentication Reef's issuer through a structured `AuthenticationConfiguration`). The owner refused it the same day: "mandar para API do cluster, acho que está errado ... a CLI deveria se comunicar com a API do Platform API, que no caso aqui é o Nereus. E tudo o resto ficaria atrás dessa API."

## Decision

**The Nereus API is the one door of the platform.** The CLI, a portal, an IDE and the agents talk to it, with the person's token from the authentication Reef (ADR 0006). Everything else sits behind it: the Kubernetes API with the Reefs' kinds, the Nereids, the tools they drive. A client never needs a kubeconfig to use the platform.

- **It runs in the cluster:** a Deployment and a Service `nereus-api` in `nereus-system`, installed by `nereus init` with the `core` Reef (owner, 2026-10-30, over a process on the person's machine or a route inside `nereus-mcp`). Its public name is `api.<domain>`, `api.getnereus.dev` for Nereus itself (#577, the edge Reef).
- **It validates the token, and only it:** the issuer and the JWKS come from the default Mandate of the authentication Reef (`status.oidc`), the audience is `nereus-api`. The Kubernetes apiserver is not taught to trust the issuer: a person's token never reaches it.
- **It acts on the cluster with its own identity** (a ServiceAccount and its RBAC), and decides what the person may do (by group, later by team) before acting.
- **It speaks of Reefs, never of tools** (ADR 0002): its routes name Reefs and their kinds, and it reads what the Nereids publish in `status`.
- **Its first slice is `GET /healthz` and `GET /v1/me`** (#607), which `nereus whoami` calls. The rest of the CLI moves behind it one command group at a time; until a group moves, its commands keep using the kubeconfig, a stand-in this ADR names.
- **A check holds the door** (#1529, owner 2026-11-14): `scripts/checks/kubeconfig-ban`, part of `make checks`, refuses any kubeconfig access in `cli/src/nereus/` (a kube context, a client built from the kubeconfig, `kubectl`) outside the files `scripts/checks/kubeconfig-allowlist` names, each with a count that may only go down. Three exceptions are permanent: `nereus init` and what bootstraps an instance on a cluster (they need that cluster's credentials), the settings of the person's own machine, and `cluster.py`, which holds the doors themselves. Every other entry is a stand-in, removed by the issue that moves its commands behind the API.

## For a new feature

Every new command, Reef or screen reaches the platform through the Nereus API, from its first slice: a route in `api/`, called by the CLI or the portal with the person's token. It never adds a line to the allowlist; a feature that seems to need the kubeconfig is either part of `nereus init` and the bootstrap, or a sign that the API lacks a route, and gets that route instead.

## Prior art

- **`wasp-idp`'s Platform API** (the project Nereus comes from, `platform/api/src/platform_api/app.py` and `auth.py`): one HTTP API for the CLI, the portal and the agents, a bearer token checked against the issuer's JWKS and the audience, `GET /v1/me` answering who the person is; the first slice and its token check are ported from it.
- **The API gateway pattern** ([microservices.io, Chris Richardson](https://microservices.io/patterns/apigateway.html)): "Implement an API gateway that is the single entry point for all clients."; the Nereus API is that single entry point, in front of the Reefs instead of services.
- **The CNCF Platforms white paper** ([TAG App Delivery](https://tag-app-delivery.cncf.io/whitepapers/platforms/)): a platform should "offer its capabilities through consistent interfaces and focus on the user experience"; one API for every client is how Nereus keeps its interfaces consistent.

## Consequences

- `nereus whoami` asks the Nereus API (#607); the `AuthenticationConfiguration` of the apiserver drafted for #605 is dropped.
- Authentication, authorization by team, policy, cost and several clusters live in one place, the API, instead of in each client and in the apiserver's configuration.
- The CLI keeps two ways to reach the platform for a while: the API for the groups already moved, the kubeconfig for the rest. Each move is its own issue; the stand-in ends when no command needs a kubeconfig. Moved: `whoami`, `doctor`, `login` (#1321); `status`, `reef`, `nereid` (#1322); `registry` but `repository publish` (#1324); `mandate`, `secrets` (#1323); `release` (#1514), its `source publish` too (#1518); `build` (#1515), `build trigger` (#1528) and `build apply` (#1594); `delivery` and `workload deploy` (#1516), `workload logs` (#1517); `tenancy` and `config set owner` (#1639); `environment` but `environment kubeconfig` (#1638).
- `nereus-mcp` became a part of the API: ADR 0029 has it serve `/mcp` with the tools the Reefs declare (#1806), and the `nereus-mcp` process, which read the cluster with the kubeconfig, is retired (#1810).
- The API is one more workload to run, secure and publish: its image, its RBAC, its hostname (#577).

## Open questions

- **How the CLI finds the API's URL:** published by the `core` Reef or set with `nereus config`, decided in #607.
- **The framework** of the API (Starlette or FastAPI with uvicorn, as `nereus-mcp`), decided in #607.

*Origin: the owner's decisions of 2026-10-30 in the session that built `nereus login` (#605): the correction of `whoami` and the choice of the API in the cluster; the raw log under `#pontos/raw/2026-10-30/`.*

*Rewritten 2026-11-14 from the owner's ban of the kubeconfig (#1529) and the request to make it the rule for every new feature; raw data in `#pontos/raw/2026-11-14/`.*
