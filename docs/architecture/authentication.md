# Authentication

Who can call `jarvisd`, and how it knows. The `auth` module owns users, households, nodes and tokens; every other module checks callers through it in process, not over HTTP.

## Callers

| Caller | Credential | Used by |
|---|---|---|
| A person | `Authorization: Bearer <access token>` (an RS256 JWT) | The mobile app, the web admin |
| A node | `X-API-Key: node_id:node_key` | Voice nodes, desktop agents |
| An external app | `X-Jarvis-App-Id` and `X-Jarvis-App-Key` | Callers outside the process, such as a remote GPU machine |
| An operator script | `X-Jarvis-Admin-Token` | `/auth/admin/*` only; unset by default, so those routes refuse everything |

Secrets are compared in constant time, and an unset expected value never matches.

## Households

A **household** is the unit everything is shared in: nodes, devices, routines, recipes. A person can belong to several households and switch between them (`POST /auth/switch-household`). A check always uses the household the request is about, not the one the token was issued for.

Each membership has a role:

| Role | Can also |
|---|---|
| `member` | Use Jarvis in the household |
| `power_user` | Create invites, add nodes |
| `admin` | Edit or delete the household, add and remove members |

Separately, a person can be a **superuser** of the whole install. Superusers use every page of the web admin; other members see only Chat and Add-ons there, and the server enforces that per route.

### The first account

On a fresh install no account exists yet. `jarvisd` writes a one-time **setup token** to `setup-token` in its data directory (readable only by the service user) and keeps only its hash in memory. The [setup wizard](../install/setup-wizard.md) at `http://<host>:7710/setup` asks for it, creates the first superuser and a household called "My Home", and the token file is deleted. If you missed the token at install, `jarvisd setup-link` prints the setup link again.

### Joining

After the first account, sign-up needs an **invite code** from a household's power user or admin. Invites grant `member` or `power_user` (never `admin`) and expire after 7 days by default. Open sign-up, where anyone who can reach the server makes an account, is off unless `auth.open_registration` is turned on.

## Passwords

- Passwords are hashed with **bcrypt** (cost 12).
- Login, sign-up and token refresh are rate-limited per IP address, and repeated failed logins for one email lock it out for a while (by default 8 failures, 15 minutes).
- A superuser can set a temporary password for someone. It is shown once, forces a new password, and signs that person out everywhere. Until the password is changed, the server refuses every other request from that account.
- Changing your password revokes every refresh token, so your other devices sign in again. An access token already issued stays valid until it expires.

## Tokens

### Access tokens

Access tokens are JWTs signed with **RS256**. They last **30 minutes** (`auth.token.access_expire_minutes`) and carry the user ID, email, superuser flag and current household.

The signing key is an RSA-2048 key that `jarvisd` generates on first start and keeps in its database. There is no key to configure. Anyone who needs to verify a token can fetch the public key:

```
GET /auth/public-key
→ {"public_key": "-----BEGIN PUBLIC KEY-----...", "algorithm": "RS256", "kid": "..."}
```

The token's `kid` header names the key that signed it. Keys are kept apart by algorithm, so a token that claims HS256 cannot be forged with the public RSA key.

!!! note "Upgraded installs"
    An install imported from the old Docker stack keeps the old shared HS256 secret, **only to verify** tokens issued before the move, so nobody is signed out. New tokens are always RS256.

### Refresh tokens

Refresh tokens last **30 days** (`auth.token.refresh_expire_days`). `jarvisd` stores only a hash of each one. Every refresh returns a new refresh token and retires the old one.

- A retired token presented again within a few seconds (`auth.token.refresh_grace_seconds`, default 10) gets the same successor, so two requests racing on a phone do not sign it out.
- Signing out revokes that session, or every session.

## Nodes

A node (a voice node or a desktop agent) has a **node ID and a node key**. It sends both on every request as `X-API-Key: node_id:node_key`.

- The key is random and shown once; `jarvisd` stores a bcrypt hash.
- A node belongs to exactly one household, and records who added it.
- A node may call only the modules it has been granted.
- Validation reads the node's state on every call, so turning a node off or signing it out takes effect at once.

### Adding a node

Every path ends at `POST /nodes/register` with a short-lived **provisioning token**:

- **Voice node:** the mobile app gets a provisioning token (valid for 30 minutes) and hands it to the node while the node is in setup mode. See [Provisioning](../clients/provisioning.md).
- **Desktop agent:** the computer shows a pairing code. A household member types that code in to approve it; the pairing list never shows the codes, and wrong guesses are limited. The computer then shows the household's name to confirm before it registers.

Signing a device out (by the person who added it, or a household admin) removes the node and revokes its credentials, for HTTP and MQTT alike.

### MQTT

The broker on port 1884 accepts a node with its node ID as the username and its node key as the password; nodes fetch these from `GET /node/mqtt-credentials`. Each node may subscribe only to its own topics (`jarvis/nodes/<node_id>/#`), and only the command center publishes commands to a node.

### Command secrets

Secrets that commands use (API keys, account tokens) are encrypted **end to end** between the mobile app and the node with the node's own key (AES-256-GCM). The command center carries the encrypted settings but cannot read them. They are edited only in the mobile app, by household admins.

## App credentials

App-to-app keys remain only for callers outside the process. Inside `jarvisd`, modules do not authenticate to each other. `jarvisd` has its own app credential (stored in `app-key` in the data directory) to sign the callbacks its own background jobs make. App keys are stored as bcrypt hashes and can be rotated or revoked.

## Accounts and deletion

Deleting an account (`DELETE /auth/me`) asks for the password, and refuses while you still have an active node or are the only admin of a household that has other members. Then, in one transaction, every module removes what belongs to you, your activity history is de-identified, and households left empty are deleted with their nodes. Data that belongs to a household stays with it.

Deleting a household (admins only) runs every module's clean-up for it and drops its nodes' cached credentials.

## Where it lives

In [jarvis-server](https://github.com/alexberardi/jarvis-server): `internal/modules/auth` (routes, tokens, households, nodes), `internal/platform/authn` (JWT checks and the caller types other modules use), and the design notes [`docs/cc/00-platform.md`](https://github.com/alexberardi/jarvis-server/blob/main/docs/cc/00-platform.md) and [`05-nodes.md`](https://github.com/alexberardi/jarvis-server/blob/main/docs/cc/05-nodes.md).
