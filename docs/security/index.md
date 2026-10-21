# Security

Jarvis Automation runs on your own hardware, and nothing that needs the internet is on by default. This page is the short version for running a server; the details are in the [security model](../architecture/security.md).

!!! tip "Staying fully local"
    Every outbound-internet capability is opt-in and defaults to off. See [Network Egress & Offline Mode](offline-mode.md) for the toggles.

## What to know as an operator

- **Three ports.** A fresh install listens on 7700 (the API), 7710 (the web admin) and 1884 (MQTT for nodes). Keep them on your home network. To reach Jarvis from outside, use a tunnel or reverse proxy with TLS instead of opening the ports.
- **Finish setup promptly.** Until the first account exists, the [setup wizard](../install/setup-wizard.md) asks for the one-time setup token from the server's data directory, so nobody else on the network can claim the server. After that, people join with an invite code.
- **Every caller is authenticated.** People sign in with a password and get short-lived RS256 tokens; each node has its own key and its own MQTT login. See [Authentication](../architecture/authentication.md).
- **Protect the data directory.** `~/.jarvisd/` (or `/var/lib/jarvisd` for the Linux service) holds the database and the token signing key, readable only by the service user. Backups contain the signing key too.
- **Command secrets stay on the node.** API keys and account tokens for commands are encrypted end to end between the mobile app and the node; the server cannot read them.
- **Updates are signed.** `jarvisd upgrade` and Update in the web admin refuse a release whose minisign signature or checksum does not match.

## More

- [Security model](../architecture/security.md): what listens, what is stored, what leaves your network.
- [Network Egress & Offline Mode](offline-mode.md)
- [Compliance Roadmap](compliance-roadmap.md)
- [Privacy Policy](privacy-policy.md)

The security page of the old Docker install is kept under [Legacy](../legacy/security/index.md).
