# Compliance Roadmap

Jarvis Automation's **default posture is self-hosted on a private network**: one program, `jarvisd`, with its data in one SQLite file (`jarvis.db`) and an embedded MQTT broker. Its ports speak plain HTTP and MQTT; to reach it from outside your home network, you put it behind a tunnel or reverse proxy that terminates TLS (see the [security model](../architecture/security.md)). That trust model fits the home and small-team installs Jarvis targets today.

This page lists what `jarvisd` already does, and what would still be needed to take it **beyond** that boundary: multi-host, enterprise and regulated deployments (HIPAA, SOC 2 Type II, ISO 27001 and similar). The planned items are **hardening for those environments, not gaps in the default self-hosted use**, and none of them is scheduled yet.

**Design principle:** security must not destroy the developer experience. Development stays easy; production is strict.

## Done

What `jarvisd` does today, with the place in [jarvis-server](https://github.com/alexberardi/jarvis-server) that does it.

| Area | What `jarvisd` does | Where |
|---|---|---|
| Tokens | Access tokens are RS256 JWTs (30 minutes) from a key generated on first start; refresh tokens rotate and are stored only as hashes | `internal/modules/auth/keys.go` |
| Passwords | bcrypt (cost 12) | `internal/modules/auth` |
| Brute force | A per-IP rate limit on login, sign-up and token refresh (30 a minute by default), and a lockout after 8 failed logins for one email, for 15 minutes | `internal/modules/auth/auth.go` |
| First run and sign-up | Creating the first account needs a one-time setup token from the data directory; after that, joining needs an invite code | `internal/modules/auth` |
| Access control | Household roles (`member`, `power_user`, `admin`) plus a `superuser` flag for the whole install; every request is checked against the caller's memberships for the household it is about | `internal/modules/auth`, `internal/platform/authn` |
| Nodes | Each node has its own key (stored as a bcrypt hash) and may call only the modules it has been granted | `internal/modules/auth` |
| MQTT | The broker requires each node's login and limits it to its own topics (`jarvis/nodes/<node_id>/#`) | `internal/platform/mqtt/auth.go` |
| Web admin headers | Content-Security-Policy, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff` and a Referrer-Policy on every admin response | `internal/modules/admin/admin.go` |
| Deletion | Deleting an account or a household removes its data in one transaction, and de-identifies the account's activity history | `internal/modules/auth/deletion.go` |
| Logs | Stored in a table in `jarvis.db`, kept for 7 days by default (`logs.retention_days`) | `internal/modules/logs/logs.go` |
| Files on disk | The data directory is 0700 and its files 0600 on Linux and macOS (`umask 077`); on Windows the directory's ACL protects it | `cmd/jarvisd` |
| Updates | Releases are checked against a minisign signature and checksums before they install; the database is snapshotted first, and a failed update rolls back | `internal/update` |
| Egress | Every outbound-internet feature of the server is off by default ([Network egress and offline mode](offline-mode.md)) | settings in each module |
| Command secrets | Encrypted between the mobile app and the node with the node's key (K2); the server stores only ciphertext, though K2 passes through its memory once for nodes keyed through it ([Command secrets](../architecture/authentication.md#command-secrets)) | `internal/modules/cc/settingsreq.go` |

## Planned

What is **not** in `jarvisd` today. Until these exist, the mitigation is the private-network posture above.

### Encryption in transit

`jarvisd` listens with plain HTTP on 7700 and 7710 and plain MQTT on 1884; there is no TLS listener.

- TLS on 7700, 7710 and 1884, with certificates the operator provides or `jarvisd` generates.
- Until then, document a supported reverse-proxy setup for each port, including MQTT.
- A production mode that refuses to start without TLS.

### Encryption at rest

`jarvis.db` and its backups are not encrypted. They hold the token signing key and some third-party credentials in the clear (remote model API keys, the Twilio credentials, the Hugging Face token); see [What is stored](../architecture/security.md#what-is-stored).

- Encrypt `jarvis.db` and its backups, or at least the secret settings, with a key kept apart from the database.
- Until then: full-disk encryption on the host (LUKS, FileVault, BitLocker) and private storage for backups.

### Audit trail

There is no audit log beyond the operational logs, which expire after 7 days.

- An append-only audit table in `jarvis.db`: sign-ins and failures, sign-ups, token refreshes, node registration and sign-out, admin actions, setting changes and deletions, with actor, household, source address and time.
- A superuser view and export, and a retention period of its own.

### Finer access control

Roles are fixed: `member`, `power_user`, `admin` per household, and `superuser` for the install.

- Permissions per resource and action, assignable roles, and service accounts.

### Sessions

- Listing a person's signed-in sessions, signing out one of them, and a cap on concurrent sessions.

### Data classification and retention

- An inventory of personal data by sensitivity (emails, memories, transcripts, voiceprints).
- Redacting the most sensitive fields from logs.
- Retention settings for conversation transcripts and memories, as there are for logs, computer recordings and call audio.

### Compliance documentation

- Policy documents: access control, encryption, incident response, data retention, change management.
- A mapping from each framework's controls to the implementation and its evidence.
- Automated checks in CI that the controls above are in place.
