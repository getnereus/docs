# kagent for Amphitrite

Amphitrite is the Nereid that will give the platform its AI agents: a Reef whose kind is `Agent` (plural `agents`), used by other Nereids for the tasks where AI does better than a deterministic step (summarise, catalogue, classify). The Agent does not name its engine: it points at a mandate that says which gateway and model to use, as a PersistentVolumeClaim points at a StorageClass, so swapping LiteLLM for OpenRouter is swapping the mandate. Triton, the coordinator of the agents, is the first Agent. "Native first, build last" ([vision](../vision.md)) asks whether an open-source tool already does this; this page evaluates [kagent](https://kagent.dev), compares it briefly with the alternatives, and records a first end-to-end run of Triton on k3d with a tiny local model through Ollama. It answers the beach order `20261028-1708-evaluate-kagent-for-amphitrite-resend`. Facts come from pages opened on 2026-10-28, linked inline and in [Learn more](#learn-more); repository figures were read from the GitHub API that day; what the run on k3d showed is marked as our own observation.

## Recommendation

**Adopt kagent as the Tool of the Amphitrite Nereid, behind a thin Nereus Reef: wrap it, do not build our own runtime and do not expose kagent's CRDs as the platform's API.**

- **Adopt the runtime:** kagent already does what we would build: a Kubernetes controller that turns an `Agent` resource into a Deployment serving the agent over A2A, a `ModelConfig` that is exactly the StorageClass-style engine object of the design, OpenAI-compatible endpoints (LiteLLM, OpenRouter) and Ollama as providers, MCP tools, memory, a UI and a CLI. It is Apache-2.0, a CNCF Sandbox project, and very active. It ran Triton end to end on k3d in minutes (below).
- **Wrap it in a Reef:** kagent's API is `kagent.dev/v1alpha2` and moving fast towards 1.0 (17 alphas in five weeks, and the chart on `main` already differs from the 0.10 docs), so other Nereids should depend on a Nereus contract, not on kagent's. The rule "the API never names a Nereid" ([rules](../agent/rules.md)) says the same: the Reef's `Agent` carries what an agent is (description, instructions, the engine's mandate, tools), and Amphitrite renders it into kagent's `Agent` and `ModelConfig`. Swapping kagent later (for Ark, say) changes the Nereid, not the Nereids that use agents.
- **Do not build our own CR runtime:** the alternatives either are not an agent definition (Agent Sandbox, Dapr Agents) or are younger and smaller than kagent (Ark, Kagenti).

## kagent

| Question | Answer |
|---|---|
| What it is | Kubernetes-native framework for AI agents: an agent is a resource the controller reconciles into a pod serving the agent over A2A ([repo](https://github.com/kagent-dev/kagent)) |
| Started by | Solo.io; CNCF Sandbox since 2025-05-22 ([CNCF](https://www.cncf.io/projects/kagent/)) |
| Licence | Apache-2.0 ([repo](https://github.com/kagent-dev/kagent)) |
| Activity (2026-10-28) | about 4.1k stars, about 213 contributors, repository created 2025-01-21; releases v0.10.4 and v1.0.0-alpha17, both 2026-10-21; 17 v1.0 alphas between 2026-09-18 and 2026-10-21; 100+ commits on the default branch in the last month ([releases](https://github.com/kagent-dev/kagent/releases)) |
| API | `kagent.dev/v1alpha2` (also serves `v1alpha1`) ([API reference](https://kagent.dev/docs/kagent/resources/api-ref)) |
| CRDs installed by chart 0.10.4 | `Agent`, `ModelConfig`, `ModelProviderConfig`, `RemoteMCPServer`, `MCPServer`, `ToolServer`, `Memory`, `SandboxAgent`, `AgentHarness` (our observation, `kubectl get crd`); the API reference documents the first four plus `SandboxAgent` and `AgentHarness`, memory as `declarative.memory` ([API reference](https://kagent.dev/docs/kagent/resources/api-ref)) |
| Agent types | `Declarative` (model, system message, tools, on kagent's runtime, `go` by default or `python`) or `BYO` (your own image serving A2A on port 8080) ([API reference](https://kagent.dev/docs/kagent/resources/api-ref); `kubectl explain agent.spec`) |
| Tools | MCP servers (`RemoteMCPServer`, up to 20 tools per agent) and other Agents as tools ([API reference](https://kagent.dev/docs/kagent/resources/api-ref)) |
| Invocation | A2A on the controller, port 8083: `/api/a2a/<namespace>/<agent>/`; `kagent invoke --agent <name> --task "..."` ([A2A example](https://kagent.dev/docs/kagent/examples/a2a-agents)) |

### Model providers: LiteLLM and OpenRouter

`ModelConfig.spec.provider` is one of `Anthropic`, `OpenAI`, `AzureOpenAI`, `Ollama`, `Gemini`, `GeminiVertexAI`, `AnthropicVertexAI`, `Bedrock`, `SAPAICore`, `Foundry` ([API reference](https://kagent.dev/docs/kagent/resources/api-ref)).

- **LiteLLM: yes.** `provider: OpenAI` with `openAI.baseUrl` takes any OpenAI-compatible endpoint; the "BYO OpenAI-compatible model" page shows kagent in front of a LiteLLM proxy ([BYO OpenAI-compatible](https://kagent.dev/docs/kagent/supported-providers/byo-openai)).
- **OpenRouter: yes by the same field, not documented.** OpenRouter has no page among the supported providers ([providers](https://kagent.dev/docs/kagent/supported-providers)); its API is OpenAI-compatible at `https://openrouter.ai/api/v1` ([OpenRouter quickstart](https://openrouter.ai/docs/quickstart)), so it is the same `openAI.baseUrl` case. Not run yet: it needs a key.
- **The path is proven:** the Triton run below uses `provider: OpenAI` with `baseUrl` pointing at Ollama's OpenAI-compatible `/v1` ([Ollama docs](https://docs.ollama.com/api/openai-compatibility)), the same mechanism LiteLLM and OpenRouter would use (our observation).
- **Ollama natively:** `provider: Ollama` with `ollama.host` ([Ollama provider](https://kagent.dev/docs/kagent/supported-providers/ollama)).
- **Caveat:** the agent sends tool definitions; a backend without automatic tool choice (vLLM without it) fails every turn with a 400 ([BYO OpenAI-compatible](https://kagent.dev/docs/kagent/supported-providers/byo-openai)).

### Install footprint on k3d

Chart 0.10.4, with the ten built-in agents, `kagent-tools`, `kmcp` and `grafana-mcp` turned off (values below), our observation:

| Pod | Image | Requests |
|---|---|---|
| `kagent-controller` | `ghcr.io/kagent-dev/kagent/controller:0.10.4`, 42 MB | 100m, 128Mi |
| `kagent-ui` | `ghcr.io/kagent-dev/kagent/ui:0.10.4`, 136 MB | 100m, 256Mi |
| `kagent-postgresql` (bundled, "for development and evaluation only") | `postgres:18.6-alpine3.23`, 120 MB | 250m, 256Mi |
| one per Agent (`triton`) | `ghcr.io/kagent-dev/kagent/golang-adk:0.10.4`, 38 MB | 100m, 384Mi |

The whole k3d node used about 970 MiB of memory with Triton running. The UI has no `enabled` flag in the chart. The default install ([installation](https://kagent.dev/docs/kagent/introduction/installation)) adds ten agents and the tool servers; `kagent install --profile minimal` installs none.

### What to watch

- **Security:** the controller's `auth.mode` defaults to `unsecure`: a caller who reaches port 8083 acts as `admin@kagent.dev` (chart values, `controller.auth`). Amphitrite must install it with `trusted-proxy` (oauth2-proxy in front) or keep the controller unreachable outside the cluster; the authentication Reef is the natural front. This is OWASP A01 (Broken Access Control) and A07 (Identification and Authentication Failures).
- **The bundled Postgres** is for evaluation only; a real install points `database.postgres.url` at a database of the platform.
- **API churn:** v1alpha2 and a 1.0 in alpha; the Reef shields the other Nereids from it.
- **Unknown:** how the 1.0 Substrate runtime changes the footprint.

## Alternatives

| Project | Licence and status | What it is | Why not first |
|---|---|---|---|
| [Ark](https://github.com/mckinsey/agents-at-scale-ark) (McKinsey) | Apache-2.0, about 432 stars, v0.1.72 on 2026-10-21 | Kubernetes CRDs `Agent`, `Model`, `Team`, `Query`, `Tool`, `MCPServer`, `A2AServer`, `Memory` ([docs](https://mckinsey.github.io/agents-at-scale-ark/)) | Closest model (a `Model` the `Agent` references, `Team` for coordination); younger and ten times smaller; the second candidate if kagent stalls |
| [Kagenti](https://github.com/kagenti/kagenti) | Apache-2.0, about 302 stars, docs at v0.7.0; the repository now redirects to `rossoctl/rossoctl` | Framework-neutral platform for agent identity, authorisation, tools and sandboxes, A2A and MCP | Its CRDs are not documented in the README; in transition |
| [Agent Sandbox](https://github.com/kubernetes-sigs/agent-sandbox) (kubernetes-sigs, SIG Apps) | Apache-2.0, about 4.4k stars, v1.0.8 on 2026-10-22 | `Sandbox`, `SandboxClaim`, `SandboxTemplate`, `SandboxWarmPool` (`agents.x-k8s.io/v1beta1`) | Runtime isolation, not an agent definition: a possible layer under Amphitrite for agents that run code |
| [Dapr Agents](https://github.com/dapr/dapr-agents) | Apache-2.0, under the CNCF Dapr project, about 767 stars, v1.1.0 on 2026-10-27 | Python framework for durable agents on Dapr | A library, no agent CRD |

LangGraph Platform and Kubeflow were not evaluated.

## Triton under the recommendation

The Reef's `Agent`, what other Nereids and the CLI write. The Reef's name and the shape of the mandate are open questions (below); this draft assumes a Reef `agent` and a second Reef `model` whose mandates are the engines (Nereids `ollama`, `litellm`, `openrouter`):

```yaml
apiVersion: agent.getnereus.dev/v1alpha1
kind: Agent
metadata:
  name: triton
spec:
  description: Triton, the coordinator (mediator) of the platform's agents.
  instructions: |
    You are Triton, the coordinator of the Nereus platform's agents.
    Answer in one short sentence.
  model:
    mandate: local        # model reef mandate: Nereid ollama, model qwen2.5:0.5b
  tools: []
```

Moving Triton to the Anthropic API later changes only `mandate:` (for example `anthropic`), never the Agent's other fields. Amphitrite renders it into kagent's objects, the ones applied by hand in the run below.

## The first end-to-end run

Agent → ModelConfig → Ollama → answer, on 2026-10-28 (our observation). The quality of the answer does not matter; the flow does.

- **Model:** `qwen2.5:0.5b` (about 400 MB), pulled into the Ollama already installed on the machine (0.20.7, systemd service on `127.0.0.1:11434`).
- **Wiring:** Ollama listens only on loopback, so a `socat` container on the host network forwards the k3d network's gateway (`host.k3d.internal`, here `192.168.240.1`) to it; Ollama's own config stays untouched. The `ModelConfig` uses `provider: OpenAI` with `baseUrl: http://host.k3d.internal:11434/v1`, the path LiteLLM and OpenRouter would take.
- **Result:** Triton answered "I am an agent designed to help users smoothly interact with Nereus, the platform for coordinating AI research." The first call took about 50 s (the model loading), the second about 5.5 s.

To reproduce:

```bash
ollama pull qwen2.5:0.5b

k3d cluster create amphitrite \
  --no-lb \
  --k3s-arg '--disable=traefik@server:0' \
  --wait

gateway="$(docker network inspect k3d-amphitrite --format '{{(index .IPAM.Config 0).Gateway}}')"

docker run \
  --detach \
  --name amphitrite-ollama-bridge \
  --network host \
  alpine/socat \
  "TCP-LISTEN:11434,bind=${gateway},fork,reuseaddr" \
  TCP:127.0.0.1:11434

cat > minimal-values.yaml <<'EOF'
providers:
  default: ollama
  ollama:
    provider: Ollama
    model: "qwen2.5:0.5b"
    config:
      host: host.k3d.internal:11434
kmcp: {enabled: false}
kagent-tools: {enabled: false}
grafana-mcp: {enabled: false}
k8s-agent: {enabled: false}
kgateway-agent: {enabled: false}
istio-agent: {enabled: false}
promql-agent: {enabled: false}
observability-agent: {enabled: false}
argo-rollouts-agent: {enabled: false}
helm-agent: {enabled: false}
cilium-policy-agent: {enabled: false}
cilium-manager-agent: {enabled: false}
cilium-debug-agent: {enabled: false}
EOF

helm install kagent-crds oci://ghcr.io/kagent-dev/kagent/helm/kagent-crds \
  --kube-context k3d-amphitrite \
  --version 0.10.4 \
  --namespace kagent \
  --create-namespace

helm install kagent oci://ghcr.io/kagent-dev/kagent/helm/kagent \
  --kube-context k3d-amphitrite \
  --version 0.10.4 \
  --namespace kagent \
  --values minimal-values.yaml \
  --wait

kubectl --context k3d-amphitrite apply -f - <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: triton-local-engine
  namespace: kagent
stringData:
  OPENAI_API_KEY: ollama # Ollama ignores the key; LiteLLM or OpenRouter need a real one
---
apiVersion: kagent.dev/v1alpha2
kind: ModelConfig
metadata:
  name: triton-local-engine
  namespace: kagent
spec:
  provider: OpenAI
  model: qwen2.5:0.5b
  apiKeySecret: triton-local-engine
  apiKeySecretKey: OPENAI_API_KEY
  openAI:
    baseUrl: http://host.k3d.internal:11434/v1
---
apiVersion: kagent.dev/v1alpha2
kind: Agent
metadata:
  name: triton
  namespace: kagent
spec:
  description: Triton, the coordinator (mediator) of the platform's agents.
  type: Declarative
  declarative:
    modelConfig: triton-local-engine
    systemMessage: |
      You are Triton, the coordinator of the Nereus platform's agents.
      Answer in one short sentence.
EOF

kubectl --context k3d-amphitrite --namespace kagent wait \
  --for=condition=Ready agent/triton \
  --timeout=300s

kubectl --context k3d-amphitrite --namespace kagent port-forward svc/kagent-controller 8083:8083 &

curl --silent http://localhost:8083/api/a2a/kagent/triton/ \
  --header 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":"1","method":"message/send","params":{"message":{"kind":"message","role":"user","messageId":"m1","parts":[{"kind":"text","text":"Who are you?"}]}}}' \
  | jq --raw-output '.result.artifacts[0].parts[0].text'
```

To clean up: `k3d cluster delete amphitrite` and `docker rm --force amphitrite-ollama-bridge`.

## Open questions

- **The Reef's name and group:** `agent.getnereus.dev` (kind `Agent`, plural `agents`) is a draft.
- **Where the model lives:** a second Reef `model` (Nereids `ollama`, `litellm`, `openrouter`, its mandates naming gateway and model) or the model as a parameter of Amphitrite's own mandate. ADR 0011 (a Mandate binds one Reef to one Nereid) fits the first: the Agent references a mandate of the `model` Reef.
- **Does Amphitrite expose kagent's tools and memory** in the first slice, or only description, instructions and model?
- **The UI and Postgres:** keep kagent's UI (no flag to turn it off) and point it at a database of the platform, or wait for the 1.0 chart.

## Learn more

- [kagent](https://kagent.dev) and its [repository](https://github.com/kagent-dev/kagent), [releases](https://github.com/kagent-dev/kagent/releases), [API reference](https://kagent.dev/docs/kagent/resources/api-ref), [installation](https://kagent.dev/docs/kagent/introduction/installation), [supported providers](https://kagent.dev/docs/kagent/supported-providers), [BYO OpenAI-compatible model](https://kagent.dev/docs/kagent/supported-providers/byo-openai), [Ollama](https://kagent.dev/docs/kagent/supported-providers/ollama), [A2A agents](https://kagent.dev/docs/kagent/examples/a2a-agents), [Helm reference](https://www.kagent.dev/docs/kagent/resources/helm/).
- [kagent at the CNCF](https://www.cncf.io/projects/kagent/).
- [OpenRouter quickstart](https://openrouter.ai/docs/quickstart) (the OpenAI-compatible base URL).
- [Ark](https://github.com/mckinsey/agents-at-scale-ark) and its [docs](https://mckinsey.github.io/agents-at-scale-ark/), [Kagenti](https://github.com/kagenti/kagenti), [Agent Sandbox](https://github.com/kubernetes-sigs/agent-sandbox), [Dapr Agents](https://github.com/dapr/dapr-agents).
- [Ollama's OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility).
