# Platform in an era of AI agents

!!! note "Notes on a podcast, not decisions"
    The topics of one podcast episode and how they map to Nereus. The gaps became ideas to refine (#2033 to #2037), in `Ideas` until the owner's triage.

**Credit:** [What does the concept of the platform mean in an era of AI agents?](https://www.thoughtworks.com/insights/podcasts/technology-podcasts/what-does-the-concept-of-the-platform-mean-in-an-era-of-ai-agents), Thoughtworks Technology Podcast, published 2026-11-12, 47 min. Host: Ken Mugrage (Thoughtworks). Guest: Abby Bangser, Principal Founding Engineer at Syntasso, where she builds [Kratix](https://docs.kratix.io/), a framework for building platforms, and leads a CNCF white paper on platforms. The page, with its transcript, was opened on 2026-11-21; the topics below are a summary in our own words, and the quotes are short. The owner brought the episode; an agent summarised it and mapped it to Nereus.

## The topics

**Platforms are not new**

- The industry swings between decentralising and centralising; after DevOps, the common tooling comes back to a central team.
- The difference from the days of Heroku and Cloud Foundry: then the platform was a third party's, now it is built inside the company.

**A puppy for Christmas**

- A new, polished Terraform module is the tip of the iceberg; patches, upgrades and drift follow.
- Handing templates to the teams hands them every Day 2.
- The answer is a managed service behind an API: the team that knows the tool controls the supply chain.

**The builders' experience**

- When the tools of the platform team are poor, the poor experience rolls downhill to the application developers.

**From golden paths to golden bricks**

- Say **why** the path meets the organisation's expectations, and give a checklist, automated where possible, to whoever leaves it.
- Build the path from composable bricks: replace one brick instead of rebuilding the path. The episode credits the phrase "golden bricks" to an unnamed source.

**Agents**

- Agents work inside the structures teams already have (stream-aligned and platform teams); they need no new interaction model (a talk by a Meta engineer at Fast Flow Conf, London, as quoted in the episode).
- They are faster consumers, without empathy: at a barrier, they go around it.
- What matters is a safe environment: clear boundaries and least-privilege permissions. A job that must be deterministic is a script, which AI can help write.

**The platform as a marketplace, not a gatekeeper**

- Specialists (security, databases) contribute capabilities without learning the central tooling, as sellers do on Etsy or the App Store.
- To contribute: an API (OpenAPI v3), documentation of who owns it, and the automation that serves a request.
- A low barrier into an experimental zone, then alpha, beta and GA deciding who can see and use a capability: shadow IT comes into the light. The episode cites the old blog post "Let a 1,000 flowers bloom and pull out 999 of them".

**A three-tier architecture**

- On top the interfaces (portal, CLI, MCP); at the bottom infrastructure as code, cloud providers, SaaS; in the middle the business process, which is the platform.
- Several platforms (control planes) per compliance zone, as a small and trim PCI zone in a cloud estate.

**The floating platform**

- Gregor Hohpe's floating platform: the platform rises as the layers below become commodity.
- When the API speaks of jobs to be done (deploy, a test environment, scale), what sits behind it can change from handcrafted infrastructure as code to an agent with clear boundaries.
- "That is their platform now, the harness": the shared harness of a team's agents is a platform.

**What breaks first with more consumers**

- Maintenance: an upgrade that becomes a ticket on every team's backlog does not scale.
- An ambiguous contract: more users mean more edge cases; start from the smallest API.

**The platform is a product**

- Its domain is what is unique to the business but common to the teams; what can be bought off the shelf, buy.

**Monday morning**

- Measure how long it takes to get a capability, and how long and how much work it takes to maintain it (a security patch, for example).

**Interfaces**

- There is no one right interface: the logic stays in the API, and CLI, portal and MCP are doors on it.

## How it maps to Nereus

**What Nereus already does the same way**

- **"Your platform, your way"** is Nereus: Kratix is a framework to build platforms, and so is Nereus; an Internal Developer Platform is one profile, ADR 0014 (a profile is a YAML file that installs a set of Reefs).
- **Golden bricks are the Reefs:** each capability is an API group installed at runtime, ADR 0010 (Reefs at runtime); a profile assembles the path from them.
- **A managed service instead of a puppy:** a resource Reef, ADR 0017 (resource Reefs), keeps the tool behind the API; `database` with the Nereid `cloudnative-pg` writes the connection Secret in `status.binding` and stays the owner of Day 2.
- **The marketplace's contribution model** is the Nereid contract with a Mandate, ADR 0011 (Reefs, Nereids and Mandates): a specialist writes a Nereid and binds it to a Reef, without touching the core.
- **Three tiers, interfaces as doors:** everything comes from the Nereus API, ADR 0018; the portal gets a screen per Reef, ADR 0022 (a Reef's screen is a Web Component its Nereid serves); MCP is a door of the API, ADR 0029 (each Reef declares its MCP tools, served at `/mcp`).
- **Agents as one more kind of consumer:** Triton, ADR 0030 (the messaging Nereid for agents), and the project's own work with agent sessions inside boundaries (journeys, guards).
- **Owner and audience:** the catalog records each Workload's `owner` and `audience`, ADR 0016 (the Reef that says what Nereus has).

**Gaps the episode points at**

- #2033 (Reef maturity at runtime: an alpha Reef is offered only to its audience), a sub-issue of #28 (how every feature is born: alpha, beta, stable).
- #2034 (profile guarantees: a profile states the expectations it meets as runnable checks, for those who leave the golden path).
- #2035 (fleet rollout and drift: one Mandate change reaches every Instance in waves, and an Instance changed by hand is reported).
- #2036 (the platform's two business metrics: time to get a resource, and time for a change to reach every Instance).
- #2037 (one installation per compliance zone: how several Nereus installations of one organisation relate).

## Learn more

- [The episode and its transcript](https://www.thoughtworks.com/insights/podcasts/technology-podcasts/what-does-the-concept-of-the-platform-mean-in-an-era-of-ai-agents) (Thoughtworks, 2026-11-12).
- [Kratix documentation](https://docs.kratix.io/) (Syntasso).
- *Platform as a Product*, the O'Reilly report by Abby Bangser, Daniel Bryant, Colin Humphreys and Cat Morris, already in [References](../references.md#platform-engineering).
