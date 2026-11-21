# Tenancy and access

Tenancy says whose each thing is, a tree of Organizations and nested Projects; access says who may do what on a node of that tree, through roles bound to teams.

## Example

The tree is two kinds of the tenancy reef, applied with [`nereus tenancy apply`](../specs/cli/reefs/tenancy.html#apply):

```yaml
apiVersion: tenancy.getnereus.dev/v1alpha1
kind: Organization
metadata:
  name: example
---
apiVersion: tenancy.getnereus.dev/v1alpha1
kind: Project
metadata:
  name: payments
spec:
  parent: {kind: Organization, name: example}
```

## Overview

<!-- diagram:tenancy:start (scripts/docs/diagrams) -->
<figure class="diagram tenancy" markdown="0">
<svg class="rh wide" viewBox="0 0 820 346" role="img" aria-label="In the Organization example, a Binding gives the Role developer to the Team payments on the Project payments; the Nereus API asks the Binding whether a User may act."><rect class="zone" x="0" y="0" width="560" height="240"/><text class="h" x="24" y="34" text-anchor="start">Organization</text><text class="m" x="160" y="34" text-anchor="start">(example, the boundary)</text><rect class="card" x="24" y="60" width="220" height="56"/><text class="b" x="134" y="84" text-anchor="middle">Project payments</text><text class="s" x="134" y="104" text-anchor="middle">(a node of the tree)</text><rect class="card" x="24" y="150" width="220" height="56"/><text class="b" x="134" y="174" text-anchor="middle">Team payments</text><text class="s" x="134" y="194" text-anchor="middle">(its members)</text><line class="ln" x1="134" y1="150" x2="134" y2="116"/><polygon class="ah" points="129.1,124.4 138.9,124.4 134,116"/><rect class="card" x="316" y="150" width="220" height="56"/><text class="b" x="426" y="174" text-anchor="middle">Binding</text><text class="s" x="426" y="194" text-anchor="middle">(gives a Role)</text><line class="ln" x1="316" y1="178" x2="244" y2="178"/><polygon class="ah" points="252.4,173.1 252.4,182.9 244,178"/><path class="ln" d="M426,150 L426,88 L244,88"/><polygon class="ah" points="252.4,83.1 252.4,92.9 244,88"/><text class="lbl" x="438" y="128" text-anchor="start">on</text><rect class="actor" x="620" y="150" width="200" height="56"/><text class="b" x="720" y="174" text-anchor="middle">Role developer</text><text class="s" x="720" y="194" text-anchor="middle">(a list of rules)</text><line class="ln" x1="536" y1="178" x2="620" y2="178"/><polygon class="ah" points="611.6,173.1 611.6,182.9 620,178"/><rect class="actor" x="316" y="290" width="220" height="56"/><text class="b" x="426" y="323" text-anchor="middle">Nereus API</text><line class="ln dashed" x1="426" y1="290" x2="426" y2="206"/><polygon class="ah" points="421.1,214.4 430.9,214.4 426,206"/><text class="lbl" x="438" y="264" text-anchor="start">may this User?</text></svg>
<svg class="rh narrow" viewBox="0 0 360 392" role="img" aria-label="In the Organization example, a Binding gives the Role developer to the Team payments on the Project payments; the Nereus API asks the Binding whether a User may act."><rect class="zone" x="0" y="0" width="360" height="296"/><text class="h" x="12" y="30" text-anchor="start">Organization</text><text class="m" x="348" y="30" text-anchor="end">(example)</text><rect class="card" x="12" y="48" width="336" height="56"/><text class="b" x="180" y="72" text-anchor="middle">Project payments</text><text class="s" x="180" y="92" text-anchor="middle">(a node of the tree)</text><rect class="card" x="12" y="136" width="336" height="56"/><text class="b" x="180" y="160" text-anchor="middle">Team payments</text><text class="s" x="180" y="180" text-anchor="middle">(its members)</text><line class="ln" x1="180" y1="136" x2="180" y2="104"/><polygon class="ah" points="175.1,112.4 184.9,112.4 180,104"/><rect class="card" x="12" y="224" width="336" height="56"/><text class="b" x="180" y="248" text-anchor="middle">Binding</text><text class="s" x="180" y="268" text-anchor="middle">(gives a Role on the Project)</text><line class="ln" x1="180" y1="224" x2="180" y2="192"/><polygon class="ah" points="175.1,200.4 184.9,200.4 180,192"/><rect class="actor" x="0" y="336" width="174" height="56"/><text class="b" x="87" y="369" text-anchor="middle">Role developer</text><line class="ln" x1="87" y1="280" x2="87" y2="336"/><polygon class="ah" points="82.1,327.6 91.9,327.6 87,336"/><rect class="actor" x="186" y="336" width="174" height="56"/><text class="b" x="273" y="369" text-anchor="middle">Nereus API</text><line class="ln dashed" x1="273" y1="336" x2="273" y2="280"/><polygon class="ah" points="268.1,288.4 277.9,288.4 273,280"/><text class="lbl" x="265" y="316" text-anchor="end">may this User?</text></svg>
</figure>
<!-- diagram:tenancy:end -->

*A binding gives a role to a team on one node; the API asks before it acts.*

## How it works

- Tenancy is a reef, `tenancy.getnereus.dev`, whose kinds come from each instance: every kind is a node with an optional `spec.parent`, and one kind, the boundary, isolates people and billing (here `Organization`).
- Whatever belongs somewhere names `owner: {kind, name}` in the tree: a Workload, an Environment, a team.
- The `authorization` reef holds access: a `Role` is a list of rules, `<reef>:<kinds>:<verbs>`, and a `Binding` gives it to a team, a position in a team or, as the exception, one User, on one node; access flows down the tree.
- The `teams` reef keeps one list of members: joining a team grants its access, leaving removes it. A person is one core `User` whatever the login, and a login with no User has no permission.
- The Nereus API asks before it acts; [`nereus can-i`](../specs/cli/reefs/authorization.html#can-i-yes) asks the same question and names the binding that grants it.

## Not this

- A Project is not a Kubernetes namespace: it nests, and one Project runs in several environments, on several clusters.
- A team is not an identity provider's group: groups are an output a Nereid may write, never the source.
- A role is not a profile: a [profile](runtime-and-profiles.md) is what an installation installs.

## Next

[The Nereus API](nereus-api.md): the door every client goes through.
