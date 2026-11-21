# Board tools

*A snapshot of 2026-11-05: versions, activity and features change, so check them again before deciding.*

GitHub Projects is poor on a phone. This page compares open source alternatives that can be self-hosted, focused on use on a phone, then on deploy and on integration with GitHub. It is material for the `board` reef ([#137](https://github.com/getnereus/nereus/issues/137)), where Vikunja may become a Nereid; nothing here is decided.

## How it was checked

Only Vikunja was tried: version 2.7.1 in a local container with SQLite and 12 sample tasks, in Chrome emulating a 390×844 phone. The other columns come from each project's documentation, source code and issues. A cell says "not checked" when none of these answered it.

What the trial left out: a real phone, dragging cards by touch, a task's detail page, and installing the PWA (its prompt appeared, the installation was not done).

## The comparison

| | Vikunja | OpenProject | Taiga | Planka | Focalboard |
|---|---|---|---|---|---|
| **Native app** | Official, in alpha, and its README discourages production use; beta on Google Play; iOS not checked | Official, in beta on iOS and Android, without boards; Kanban is only a backlog item (MOB-855) | None official; a third-party Android app | Not in Community | Not checked |
| **Responsive web, PWA** | Yes: a web manifest and an "add to home screen" prompt | The documentation calls it fully responsive; not tried; no PWA mentioned | No: the viewport meta tag is commented out in `app/index.jade`, and "Need responsive for mobile" (taiga-front #93) is open | Phones and tablets are a Pro feature | Not checked |
| **Kanban on a small screen** | Good in the trial: 300 px columns with scroll snap, the next column visible, no horizontal overflow of the page | Not checked | Poor, from the code and the issues | Community has open bugs: "cards do not open on mobile" (#1282), a card modal too large (#190) | Not checked |
| **Deploy** | One container with SQLite; it exits at start when its data directories are not writable | Compose or an all-in-one container | Compose with 9 services, two of them RabbitMQ | Compose with 2 containers (app and Postgres) | Not maintained |
| **Resources** | Light: about 70 MiB measured, nearly idle; a 184 MB image | Heavy: an official minimum of 4 GB and 4 cores | Medium: 1 GB minimum for the install from source; one user reports 1.5 GB in use | Light, not measured | Not checked |
| **GitHub** | None: imports from CSV, Microsoft To Do, Planka, TickTick, Todoist, Trello and WeKan; a REST API and outgoing webhooks | Links PRs to work packages; does not import issues | The best: an importer for issues, comments and history, and a webhook | None; a REST API and webhooks | Not checked |
| **License** | AGPL-3.0 (app: MIT) | GPL-3.0 | MPL-2.0 (back), AGPL-3.0 (front) | Fair Use License: source available, not open source | Source: AGPL-3.0 or commercial; compiled: MIT |
| **Activity** | v2.7.1, 2026-10-20 | v17.9.6, 2026-10-30 | Recent fixes in the back; `taiga-docker` at 6.9.0 since 2025-10 | v2.3.1, 2026-11-05 | "Currently not maintained"; last release 2024-06 |

## Reading it

1. **Vikunja** is the only free and open source option with a board proven usable at phone width, and it is the lightest. Use its PWA rather than the app in alpha. Its gap is GitHub.
2. **OpenProject** has no boards in its app and asks for 4 GB for a Kanban problem.
3. **Taiga** has the best import and fails the main criterion. It fits only if migrating the issues weighs more than the phone.
4. **Planka** leaves phones to its paid plan, and its license is not open source.
5. **Focalboard** is the negative baseline: its own README says it is not maintained, which is enough to rule it out.

## The open idea

Since Vikunja does not know GitHub, the integration may live in the platform: a process that copies issues from one to the other ([#1029](https://github.com/getnereus/nereus/issues/1029)). `scripts/board/queue` (690 lines) calls GitHub directly and holds the WIP limit and `claim`, so replacing GitHub as the source of truth would mean rewriting it, while a copy would not.

## Sources

| Tool | Documentation | Repository |
|---|---|---|
| Vikunja | [Docs](https://vikunja.io/docs/), [migration](https://vikunja.io/docs/migration-from-third-party-services), [webhooks](https://vikunja.io/docs/webhooks) | [vikunja](https://github.com/go-vikunja/vikunja), [app](https://github.com/go-vikunja/app) |
| OpenProject | [Requirements](https://www.openproject.org/docs/installation-and-operations/system-requirements/), [mobile app](https://www.openproject.org/docs/mobile-app-guide/), [app platforms](https://www.openproject.org/docs/mobile-app-guide/devices-platform/), [GitHub integration](https://www.openproject.org/docs/system-admin-guide/integrations/github-integration/), [boards](https://www.openproject.org/docs/user-guide/agile-boards/), [roadmap](https://community.openproject.org/projects/OP/roadmap) | [openproject](https://github.com/opf/openproject) |
| Taiga | [Install](https://docs.taiga.io/setup-production.html), [importers](https://docs.taiga.io/importers.html), [mobile app proposal](https://community.taiga.io/t/proposal-mobile-app/257) | [taiga-back](https://github.com/taigaio/taiga-back), [taiga-front](https://github.com/taigaio/taiga-front), [taiga-docker](https://github.com/taigaio/taiga-docker) |
| Planka | [Docs](https://docs.planka.cloud/docs/welcome/), [Pro](https://planka.app/pro), [license guide](https://github.com/plankanban/planka/blob/master/LICENSES/PLANKA%20License%20Guide%20EN.md) | [planka](https://github.com/plankanban/planka) |
| Focalboard | [README with the notice](https://github.com/mattermost-community/focalboard#readme), [license](https://github.com/mattermost-community/focalboard/blob/main/LICENSE.txt) | [focalboard](https://github.com/mattermost-community/focalboard) |
