# Specs

The specs of Nereus: the plan or the design of one slice, written before its code. The command specs, one file per reef, are the [CLI reference](../specs/cli/index.html).

| Spec | Status | What it settles |
|---|---|---|
| [0001. First slice](../specs/0001-first-slice.md) | Done | `init`, a Nereid list and a fake Nereid that publishes commands |
| [0002. Reef at runtime](../specs/0002-reef-at-runtime.md) | Done | A reef added from the CLI and a Nereid installed into it from its image label |
| [0003. Nereid conformance](../specs/0003-nereid-conformance.md) | Proposed | What a Nereid image declares and how the platform checks it |
| [0004. Init time SLO](../specs/0004-init-time-slo.md) | Proposed | A fitness function caps how long `nereus init` takes |
| [0005. Cloud reef](../specs/0005-cloud-reef.md) | Accepted | How the platform presents itself to a cloud, with no credential kept |
| [0006. Installation identity](../specs/0006-installation-identity.md) | Proposed | A name, an id and an alias for each installation |
| [0007. Invitation](../specs/0007-invitation.md) | Proposed | A link and a QR code that let one person in, for a while |
| [0008. Portal first slice](../specs/0008-portal-first-slice.md) | Proposed | A PWA that says who you are |
| [0009. Build security](../specs/0009-build-security.md) | Accepted | What a hostile Dockerfile can reach in the build reef |
| [0010. Build trigger](../specs/0010-build-trigger.md) | Proposed | A new commit on a Mirror builds a Workload |
| [0011. Authorization first slice](../specs/0011-authorization-first-slice.md) | Proposed | The first slice of teams and authorization |
| [0012. Presentations first slice](../specs/0012-presentations-first-slice.md) | Not stated | Drive and follow: a phone drives a Session, others follow |
