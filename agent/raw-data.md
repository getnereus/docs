# Raw data

The raw material of the project (voice sessions, transcripts, mental dumps, the agents' session logs, work orders) lives outside the repository, in the owner's Google Drive. Since 2026-11-08 the raw session data is in one place, and the work orders keep their own folder.

- `#pontos/raw/<YYYY-MM-DD>/`: one raw folder per day, holding both origins side by side, told apart by the name: `HHMM-voice-<slug>.<ext>` for the owner's voice sessions (recordings, transcripts, the messages between the voice session and the local agent, and their classifications next to the notes), and `HHMM-m15-...` for the Claude Code session logs that Pontos saves. The time prefix orders the day.
- `#pontos/silver/classification/`: the machinery of the daily classification by a Haiku model (`classification-rules.md`, `topics.yaml`, the watermarks, the grades, the worklists and the reports). The classification of a single note stays next to the note in `raw/`; the rules, the state and the reports of the run live here.
- `#pontos/beach/` (formerly the Drive folder `dump-mental-prompts`, removed on 2026-11-08): work orders sent by the voice session to the local agent (see [Beach](beach.md)).
- `#pontos/beach/bridge/`, `opinions/`, `proposals/` and `references/`: unchanged (the bridge between the sessions, the opinions and research files of a design session, the agents' proposals, the reference notes).

The raw logs of the agents' own sessions are not this repository's concern: on the owner's machines, Pontos, a set of hooks in the owner's personal Claude Code settings, saves every session of the owner's repositories to `#pontos/raw/<date>/`. A contributor's sessions are saved nowhere; an agent writes nothing to Drive for it.

Rules:

- Read it with `rclone` (`rclone lsf gdrive:#pontos/raw/<date>`, `rclone cat ...`); the FUSE mount is slow. Find a voice note of a day with `rclone lsf gdrive:#pontos/raw/<date> --include '*-voice-*'`.
- Raw data is private. The repository is public by design (ADR 0007): copy into it only the decision or the method, never names, figures or personal data. An ADR or spec may cite the raw file by its path in the folder (`#pontos/raw/<date>/HHMM-voice-<slug>.md`).
- When a session creates an idea or moves one on the [idea radar](../project/roadmap.md), the summary of its raw log carries a `Radar: <ring>` line (In Nereus, Refining, Exploring or Parked), and the radar's row moves in the next pull request.

## Drive access: our own OAuth client

rclone reaches Drive through the `gdrive` remote, and Pontos, the beach and the bridge folder all depend on it. rclone's shared Google client_id is retired during 2026, so the remote runs on an OAuth client of the owner's own (smsilva/linux#89, done on 2026-10-31). On a new machine, or when the client changes, set it up once:

1. **Project:** in the Google Cloud console, create a project (`rclone-gdrive`) and enable the Google Drive API in it.
2. **Consent screen** (Google Auth Platform):
   - Branding: app name `rclone`, the support and developer contact e-mails, and an application home page and privacy policy link (the repository's URL is enough). Without the two links, Publish app stays disabled.
   - Audience: External, then Publish app. In Testing, the token expires every seven days and Pontos stops uploading.
   - Data Access: the scope `https://www.googleapis.com/auth/drive`.
   - The "requires verification" warning can stay: verification only matters for an app other people use.
3. **Client:** Clients, Create client, type Desktop app, name `rclone`. Download the JSON before closing the dialog, since the secret is shown once. Keep it in a secret store (the owner keeps it in a key vault as `rclone-gdrive-oauth-client`), never in a repository or a session's transcript, and delete the downloaded file.
4. **Apply** in a terminal of your own, outside any Claude Code session, since a session's log goes to Drive:

```bash
json="$(az keyvault secret show --vault-name <key vault> --name rclone-gdrive-oauth-client --query value --output tsv)"
GDRIVE_CLIENT_ID="$(jq --raw-output .installed.client_id <<< "${json}")" \
GDRIVE_CLIENT_SECRET="$(jq --raw-output .installed.client_secret <<< "${json}")" \
  ~/.scripts/gdrive-mount
```

`gdrive-mount` (smsilva/linux) switches the remote to the client, reconnects it in the browser (answer `y`; on "Google hasn't verified this app", choose Advanced, then Go to rclone) and restarts the mount. Its last line reads `client_id...: own (...)`, and `rclone lsf gdrive:#pontos` no longer prints the shared client_id's NOTICE.
