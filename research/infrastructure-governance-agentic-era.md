# Infrastructure governance in the agentic era

!!! note "Notes on a report, not decisions"
    The topics of one industry report and how they map to Nereus. The gaps became ideas to refine (#2042 to #2044) and comments on #2035 and #2036, in `Ideas` until the owner's triage.

**Credit:** *Infrastructure governance for platform teams in the agentic era*, an "Enterprise in Practice" report of 28 pages by Sam Barlien (researcher at Weave Intelligence, the research arm of platformengineering.org, and co-host of PlatformCon), published by [Weave Intelligence](https://weaveintelligence.io) in 2026 (the PDF is dated 2026-11-06) and commissioned by env zero, the company formed by the merger of env zero and CloudQuery in March 2026. env zero supplied briefings and reviewed the report for accuracy about its own products; the conclusions are Weave Intelligence's. The survey figures come from Weave Intelligence's own [State of AI in Platform Engineering 2026 (Volume 2)](https://weaveintelligence.io/research/state-of-ai-in-platform-engineering-2026), 350 respondents. Read from the PDF the owner downloaded on 2026-11-21; no public URL of the report was found that day.

The four capabilities the report proposes match what its sponsor sells (a store of every cloud resource, IaC governance and a knowledge graph on top): read them as one vendor-backed view, useful for its framing.

## The topics

**The estate stopped matching the code**

- The 2 a.m. database: an on-call engineer resizes it in the console, the fix never reaches the code, and the next `terraform apply` puts the old size back three weeks later. It happened at Razorpay (an Auto Scaling Group's image, rolled back by an unrelated apply).
- With agents, the same story lands on day two: an agent asked to cut costs finds an instance bigger than its code says, with no owner and no note, and shrinks it.
- The dangerous problems are the silent ones: a bucket left open, a server in an unapproved region, a forgotten test cluster, a deleted backup.

**What practitioners report (the survey)**

- 65% use AI to generate infrastructure as code; 43% name agents bypassing security controls as a major threat.
- 35% validate AI-generated changes by human review alone, against 17% with automated validation loops. Validation has to become a loop: an agent proposes, a deterministic gate verifies, and the system that produces a change is not the one that validates it.
- An agent on a borrowed human login "cannot be audited, scoped, or switched off without switching off the person it borrowed from". Caroline Wong (PlatformCon 2026): "You can't govern agents that you don't know exist", the shadow-agent problem. Agent identities and scopes belong in declarative definitions, so an unknown agent shows up as a mismatch, as drift does.

**What deploy-time policy never promised**

- A deploy-time check governs the pipeline, not every route into the cloud: console fixes, scripts and agents holding credentials never meet it. An old example: Salesforce, May 2021, a global DNS change through the emergency break-fix process and about five hours of unreliable logins.
- Three things are missing: the **implication** (a drift report weighs a struggling database like a retagged test bucket), the **owner** (an unowned divergence waits in a ticket queue, the TicketOps anti-pattern) and the **context** (an agent fills the gaps with whatever the reachable APIs show).
- "The platform supplies the determinism": probabilistic reasoning inside deterministic guardrails, the question moved from model quality to system structure.

**Shift down, and the four levels**

- *Shift down*: the step past shift left, where a capability is embedded in the platform instead of pushed earlier onto its users.
- At Level 2 (human on the loop) every agent pull request waits for a person; at Level 3 (human as orchestrator) the platform's gates check and people handle the exceptions. The survey places the return on agents at Level 3.
- The path is gradual: low-risk classes of change are promoted by codified rules, consequential ones (blast radius, cost, policy class) keep human verification. Two decisions stay with people on purpose: granting or widening a non-human actor's scope, and owning the exceptions. Oleg Danilyuk (VP, env zero): what matters is the scope an actor has, not whether it is a person or an agent.

**Four things the platform has to provide**

- One view of declared and running state, held as current, queryable data: an agent and an engineer asking the same question get the same answer.
- Ownership and relationships as platform data (a service catalog, an ownership file), not tags: "A tag records what someone typed, while ownership records what teams agreed."
- Attributable, scoped actors: each agent with its own identity, its scope declared as code, no borrowed credential.
- Every change goes through code: fixes land as pull requests against the owning code; a change made outside is reverted or codified back, and a resource created outside is brought into code or removed.

**Next steps and readouts**

- Five steps in order: see what is running, record ownership, scope each agent before write access, route fixes through code, start agents on low-risk work. Each human override is data about where the rules stop being trustworthy.
- Three readouts from the first month: the share of running resources with a declared counterpart, the share of the highest-risk resources with a recorded owner, and the count of agents holding write access without an identity of their own.

## How it maps to Nereus

**What Nereus already does the same way**

- **One route in:** ADR 0018 (the Nereus API is the one door; CLI, portal and agents talk to it, the Kubernetes API stays behind it); MCP is a door of the same API, ADR 0029 (each Reef declares its MCP tools, served at `/mcp`). An agent and a person get the same answer.
- **Declared and running state in one object:** ADR 0005 (`spec` written by the API, `status` by the Nereid), with continuous reconciliation.
- **Ownership as data, not tags:** `owner: {kind, name}` points to the tenancy tree, ADR 0015 (a tenancy Reef with one fixed shape), on the catalog's Workloads and Packages, ADR 0016 (each Workload with its `owner` and its `audience`, which may include `agents`), on Environments and Instances.
- **The credential stays with the platform:** ADR 0017 (the provider is named in the Mandate) and ADR 0023 (an external registry's push credential is read by the Nereid, never on the person's machine); the platform proves itself through a Mandate, ADR 0006.
- **Attribution:** ADR 0030 (Triton behind the Nereus API) adds `Principal.agent`, so the audit log says "person X, agent Y, via mcp".
- **Generation kept apart from validation:** the project's deterministic pillar (guards, hooks, `make checks`), and the journeys' decision envelope (🟢 decide, 🟠 report, 🔴 wait for the owner), an exception-based review of the agents' own work.

**Gaps the report points at**

- #2042 (agents as subjects of their own: each agent declared with an identity and a scope, and an unknown agent reported). Today an agent acts on the person's token and only names itself in a header; ADR 0027 leaves `Member.spec.kind: agent` and token exchange for later.
- #2043 (resources outside Nereus: a Reef lists what its tool runs without an Instance, and a person adopts or ignores it).
- #2044 (change classes: a rule decides which requests pass on the gates alone and which wait for a person, and each override is recorded).
- A comment on #2035 (fleet rollout and drift): a drift's implication, its route to the owner, and revert-or-adopt decided per kind.
- A comment on #2036 (the platform's business metrics): the report's three readouts.

## Learn more

- [Weave Intelligence](https://weaveintelligence.io), the publisher, and its [State of AI in Platform Engineering 2026](https://weaveintelligence.io/research/state-of-ai-in-platform-engineering-2026), the survey behind the figures, already in [References](../references.md#ai-and-agents).
- The report's sources: Saijal Shrivastava, ["The Dark Side of Terraform: Drifts, Chaos, and the Headaches They Bring"](https://engineering.razorpay.com/the-dark-side-of-terraform-drifts-chaos-and-the-headaches-they-bring-186ce3a068b6) (Razorpay Engineering, 2025); Caroline Wong, ["Security by design for agentic AI"](https://youtu.be/4aid1uNBLGw) (PlatformCon 2026); ["That Salesforce outage"](https://www.theregister.com/2021/05/19/salesforce_root_cause) (The Register, 2021). The report's footnote numbers do not match its text from note 3 on; the list above follows the sources, not the numbers.
- *Thinking in Platforms*, by Kaspar von Grünberg and Luca Galante (Weave Intelligence), already in [References](../references.md#platform-engineering).
