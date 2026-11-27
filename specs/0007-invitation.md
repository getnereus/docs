# 0007. Invitation: a link and a QR code that let one person in, for a while

**Status:** Proposed (2026-10-26)

From the owner's voice session of 2026-10-26 (raw data in Drive `#pontos/raw/2026-10-25`, voice files 113 to 119; order 20261026-0610), and the invitation slides of the first PoC's walkthrough deck (found by order 20261026-0042), ported after a public-by-design pass (ADR 0007).

## Intent

The first dive is a recorded conversation between two people on one Nereus. The owner has to let the second person in during the call, with no account set up beforehand: an invitation shown as a QR code on the screen, accepted on the phone through single sign-on (SSO), with access that ends by itself.

The slice is the walking skeleton of people coming into Nereus: one command prints a link and its QR code, accepting it creates the person as a `User` of core (ADR 0006), and both the invitation and the access it grants expire, each on its own clock. That access ends on its own, in front of everyone, is part of what the slice shows.

**Simple on the surface, consistent underneath** (the owner's design principle, voice file 113): the root form `nereus invitation create` is the familiar, welcoming one; underneath, the invitation is a kind of the `authentication` Reef with the same verbs, output and errors as every other noun (ADR 0013).

## The scene that ends the slice

```bash
# On the owner's machine: invite one person; the QR code goes on the screen of the call
nereus authentication invitation create dive-01 \
  --to maria@example.com

# The same command, through the root alias
nereus invitation create dive-01 \
  --to maria@example.com

# Maria scans the QR code, signs in with Google through SSO, and lands in Nereus as a User

# The owner sees who accepted and until when the access lasts
nereus authentication invitation get dive-01

# 24 hours after accepting (2 minutes with --access-expires 2m, in a demo), Maria's next call is refused
nereus status
```

What `create` prints:

```text
invitation/dive-01 created
to:       maria@example.com
link:     https://nereus.example.com/invitations/accept#k7Qp3...
expires:  in 5m (06:47) · the link and the invitation
access:   24h after accepting

[the QR code of the link, drawn in the terminal]

Next steps:

  nereus authentication invitation get dive-01
```

## The commands

The canonical form lives in the Reef (ADR 0013, ADR 0010): `nereus authentication invitation <verb> <name>`. The root form `nereus invitation <verb>` is an alias: the CLI runs exactly the same command, the way `kubectl` aliases do, and never adds behaviour of its own. Docs, `--help`, `--examples` and errors always show the canonical form; aliases exist only for the most used actions (voice file 113).

| Verb | Does |
|---|---|
| `create <name>` | Creates the invitation and prints its link and QR code; fails when it exists, listing `apply` and `delete` (ADR 0013). |
| `apply <name>` | Creates it, or, while nobody has accepted it, issues a new link with a new expiration: the old link stops working (`invitation/dive-01 configured`). Refused once accepted, naming `create` with another name. |
| `get <name>` | Shows one: to whom, the state (`pending`, `accepted`, `expired`), when it expires, who accepted it and until when their access lasts. Never the link. |
| `list` | One row per invitation: `NAME`, `TO`, `STATE`, `EXPIRES`, `ACCESS`, `AGE`. |
| `delete <name>` | Closes the door: the link stops working at once. It expels nobody: whoever accepted keeps their access until it expires (from the first PoC). |

The options of `create` and `apply`:

| Option | Default | Meaning |
|---|---|---|
| `--to <email>` | none | The only verified e-mail that may accept it. Without it, any verified e-mail of the authentication Mandate's allowed domains may. |
| `--invitation-expires <duration>` | `5m` | How long the link stays valid. The link (and its QR code) and the invitation are the same thing: unused in time, create another. |
| `--access-expires <duration>` | `24h` | How long the access lasts, counted from accepting. |
| `--qr-file <path>` | none | Also saves the QR code as a PNG, to show in a call. |
| `--dry-run` | | Shows the object that would be created, with `link: <generated on create>`, and changes nothing. |
| `--examples` | | The examples, each with a line saying what it does. |

`--invitation-expires` and `--access-expires` replace the first PoC's `--expires` and `--access-for`: two expirations, each named for what it ends, so nobody has to guess which one a flag sets (voice file 115). "Expires" rather than "expiration", since the value is a duration and reads as "expires in 24h".

**Durations follow Go's** ([`time.ParseDuration`](https://pkg.go.dev/time#ParseDuration)), with `d` added: one or more numbers each followed by `s`, `m` (minutes), `h` or `d`, such as `90s`, `30m`, `1h30m`, `2d`. There is no month unit, since `m` already means minutes: thirty days is `30d`. Validated with `re.fullmatch(r"(\d+[smhd])+", value)`, and the total must be greater than zero.

The QR code is drawn with [segno](https://segno.readthedocs.io/), the open source library `docs/presentations/render-outline` already uses: `QRCode.terminal(compact=True)` in the terminal, `QRCode.save(path)` for `--qr-file` (PNG with no other dependency). With `--output json` or `yaml`, the output carries the link and leaves the QR code out.

## Accepting

1. The link opens a page served by core: `https://<the API's public host>/invitations/accept#<token>`.
2. The page sends the person to sign in through the authentication Reef's default Mandate (Keycloak brokering Google, ADR 0006), keeping the token in the browser.
3. Back from the login, the page posts the token. Core checks, in this order: the token's hash matches an invitation; it has not expired; nobody accepted it; with `--to`, the token's verified e-mail is exactly that address; without `--to`, the verified e-mail's domain is one the Mandate allows.
4. Core creates the `User` (ADR 0006: the platform generates its id, and the identity is the token's issuer and `sub`) with the access's end, and writes the acceptance in the invitation's `status`. The page says until when the access lasts.

From then on, any client of the API (the CLI's `nereus login`, the claude.ai connector of the API's `/mcp`) works as that User until the access ends. After that, every call is refused with ADR 0012's message.

**Accepting creates the person in core, never in Keycloak** (voice file 116). Core owns users and their linked identities (issuer and subject); an identity provider (Keycloak, Auth0) is a Nereid that only proves "this person is this subject at this provider". Swapping the provider loses no User.

**An identity is never linked by e-mail.** If the signed-in identity already belongs to a User, accepting is refused ("you already have access here; sign in"). Linking a second identity to a User is out of this slice; when it comes, it happens only while signed in with an identity the User already has, or by an admin (voice file 116).

## The objects

`Invitation`, a kind of `authentication.getnereus.dev/v1alpha1` (ADR 0009), in the nereus namespace:

```yaml
apiVersion: authentication.getnereus.dev/v1alpha1
kind: Invitation
metadata:
  name: dive-01
spec:
  to: maria@example.com
  expiresAt: "2026-10-26T06:47:00-03:00"
  accessExpires: 24h
  tokenHash: sha256:9f2c...
  createdBy: u-7f3k2p
status:
  acceptedAt: "2026-10-26T06:44:12-03:00"
  acceptedBy: u-2m8q4x
  accessExpiresAt: "2026-10-27T06:44:12-03:00"
```

| Field | Written by | Meaning |
|---|---|---|
| `spec.to` | the API, from the CLI | The only e-mail that may accept; absent for an open invitation. |
| `spec.expiresAt` | the API, from `--invitation-expires` | When the link stops working; `apply` moves it with a new token. |
| `spec.accessExpires` | the API | The access's length, as given. |
| `spec.tokenHash` | the API | The SHA-256 of the link's token. The token itself is printed once and stored nowhere. |
| `spec.createdBy` | the API | The User who created it. |
| `status.acceptedAt`, `status.acceptedBy`, `status.accessExpiresAt` | core | The acceptance, written once. |

One writer per field (ADR 0005): the API writes `spec`; core writes `status`, as the static Nereid it exposes itself as (voice file 117, below). Core writes the acceptance with the object's `resourceVersion`, so two people racing for one invitation cannot both get in.

`User` (core, ADR 0006) gets two fields, written by core: `spec.invitation` (the invitation it came from) and `spec.accessExpiresAt`. Removing `spec.accessExpiresAt` makes the access permanent; the command that does it comes with the `nereus user` commands.

**Core exposes itself like a Nereid** (voice file 117): listed with the others, with the same contract, but static, neither replaceable nor deletable, the way the kubelet starts static pods and the API server shows them as mirror pods ([Kubernetes, static pods](https://kubernetes.io/docs/tasks/configure-pod-container/static-pod/)). For now it runs inside the API, with no deployment of its own.

## Errors

Every message says what happened and how to fix it (ADR 0012), and shows the canonical form:

```text
$ nereus authentication invitation create dive-01
✗ invitation dive-01 already exists (pending, expires in 3m). Run one of:
  nereus authentication invitation apply dive-01   # a new link; the old one stops working
  nereus authentication invitation delete dive-01  # close it

$ nereus authentication invitation create dive-02 --access-expires 1mo
✗ --access-expires 1mo is not a duration. Use numbers with s, m (minutes), h or d, such as 30m, 2h or 30d; there is no month unit.

$ nereus invitation create dive-03
✗ the authentication reef is not installed. Install it with:
  nereus init --profile internal-developer-platform

$ nereus status
✗ your access to this Nereus ended at 06:44, as set by invitation dive-01. To come back, ask for a new invitation.
```

On the acceptance page: an expired or deleted invitation says so and asks for a new one; an e-mail that is not the invited one is refused without showing the invited address; a domain outside the allowed ones names neither the domains nor the invitation's address.

## From the first PoC

| The first PoC | This slice |
|---|---|
| `platform authentication invite create` | `nereus authentication invitation create <name>`, with the root alias `nereus invitation create`; the noun `invitation` was decided on 2026-10-22. |
| `--expires` (the invite), `--access-for` (the guest's access) | `--invitation-expires` (default `5m`), `--access-expires` (default `24h`). |
| `--guest <email>`, a nominal invitation, always with a deadline | `--to <email>`. |
| `--type qr`, the QR code in the terminal for a kickoff | Always printed; `--qr-file` saves it. |
| SSO plus the e-mail verified and in `allowedDomains` as the real gate | Kept: the invitation says where you go; SSO says who you are. |
| `invite delete`: closes the door, expels nobody | Kept. |
| The guest's access ending mid-conversation, with a message that says what happened and what to do | Kept, through ADR 0012. |
| `--organization`, `--project` | Left out: Nereus has neither yet (#21). |
| `--max-uses`, `--type email`, a directory target (an OU, a group) | Left out of the first slice: one invitation lets one person in. |
| The evaluation licence, its waiting queue and `license get` | Parked as an idea (below). |

## Out of this slice

- **Sending the invitation by e-mail.** The first dive needs only the QR code and SSO; e-mail delivery comes through a notification Reef, and only if it is easy (voice file 118).
- **Evaluation licences with a waiting queue** (voice files 118, 119): a demo instance limited to a few users, the next ones waiting on a screen until the representative approves more seats from a push notification, all audited and replayed. Kept as an idea, back when the sales demo is built.
- **`--max-uses`** and invitations for many people at once.
- **Linking a second identity** to a User, and **making an access permanent** from the CLI (`nereus user` commands).
- **Who may create invitations** beyond the installation's admins: comes with authorization.

## Security and quality attributes

Under the lens of the [OWASP Top 10:2025](https://owasp.org/Top10/2025/), this slice touches:

- **A01 Broken Access Control.** Core checks every condition when accepting, not the page: the token, the expiration, single use (the `resourceVersion` write), the invited address or the allowed domains. The access ends on the server, at `spec.accessExpiresAt`, whatever the client holds. Only admins create invitations.
- **A04 Cryptographic Failures.** The token has 256 random bits (`secrets.token_urlsafe(32)`); only its SHA-256 is stored, so reading the object does not reveal a link that works. It travels in the URL's fragment ([RFC 3986, section 3.5](https://datatracker.ietf.org/doc/html/rfc3986#section-3.5)), which browsers do not send in the request line, so it stays out of access logs and proxies.
- **A06 Insecure Design.** A shared QR code alone is weak: a photo can leave the call. SSO is the real gate, the link lasts 5 minutes by default, it lets one person in, and `delete` closes it at once.
- **A07 Authentication Failures.** No identity is linked by e-mail (account takeover); a User comes only from an invitation accepted with a verified e-mail. The accepting identity must not belong to another User.
- **A09 Security Logging and Alerting Failures.** Core records a Kubernetes Event on the invitation for every create, new link, acceptance, refusal (with its reason, never the token) and delete; the platform's own audit trail and its replay come later.

Fitness functions of the slice: unit tests of the duration rule, of the checks in the acceptance order above, of the single-use race, and of the alias running the canonical command; a `test/scene` step that creates an invitation, accepts it with a test identity, and sees a call refused once a `--access-expires 5s` access ends.

## Open questions

- ADR 0006 links a new `sub` only after an e-mail code; voice file 116 links a new identity only while signed in with an existing one, or by an admin. Which one holds, or both?
- Should `--invitation-expires` have a maximum (for example `7d`), so a link cannot live for months?
- Is `--qr-file` the right name for saving the QR code as an image?

## Learn more

- **The two expirations, the nominal guest invitation and "closes the door, expels nobody"** come from the first PoC's walkthrough deck (2026-10-22).
- **Durations:** Go's [`time.ParseDuration`](https://pkg.go.dev/time#ParseDuration), whose units are `ns`, `us`, `ms`, `s`, `m` and `h`; this slice keeps `s`, `m` and `h` and adds `d`.
- **QR codes:** [segno](https://segno.readthedocs.io/), a QR code library in pure Python.
- **Identity brokering:** [Keycloak, Server Administration Guide](https://www.keycloak.org/docs/latest/server_admin/index.html), where Keycloak brokers an external identity provider such as Google.
- **Static pods and mirror pods:** [Kubernetes documentation](https://kubernetes.io/docs/tasks/configure-pod-container/static-pod/); the analogy for core was brought by Claude (Anthropic) in voice file 117.
- **Security categories:** [OWASP Top 10:2025](https://owasp.org/Top10/2025/).
