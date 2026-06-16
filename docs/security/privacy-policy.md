# Privacy Policy

**Last updated:** June 15, 2026

This privacy policy describes how Jarvis Automation ("we", "us", "Jarvis") handles information collected through the Jarvis platform, including the **Jarvis Automation** mobile app, the self-hosted backend services, and optional cloud services.

Jarvis is **self-hosted by default**. Most data flows in Jarvis never reach servers operated by us — they stay on hardware you own and operate. This policy distinguishes between the two cases.

## Summary

| Data | Where it goes | When |
|------|---------------|------|
| Voice recordings | Your own server (Whisper STT) | Always |
| Voice transcripts and assistant replies | Your own server (Command Center) | Always |
| Account credentials (email, password hash) | Your own server (Jarvis Auth) | Always |
| Authentication tokens on the mobile app | Encrypted in your device's OS keychain | Always |
| Pantry package metadata | Jarvis Automation cloud (Pantry service) | Only when you use the package store |
| Google account data (Calendar, Drive, Gmail, Nest) | Google, then your own server | Only when you enroll OAuth |
| Local network scan results (Wi-Fi SSIDs, device IPs) | Your device only | During node provisioning |
| Camera images (QR codes) | Your device only (transient) | During node pairing |

We do not sell your data. We do not run analytics on the mobile app or the self-hosted backend.

## Information you provide

**Account information.** When you create a Jarvis account, you provide an email address and password. These are stored on the Jarvis Auth service. If you are self-hosting, this is your own server. If you are using a managed Jarvis instance, this is the host you connect the mobile app to.

**Voice input.** Voice commands you speak to a Jarvis node are recorded, transcribed by the Whisper service, and processed by the Command Center. All of this runs on the server you have configured.

**Configuration data.** Node names, room assignments, device pairings, routines, and similar settings are stored on your own server.

**Optional integrations.** If you enroll third-party services (Google Calendar, Gmail, Drive, Nest, Home Assistant, etc.), you authorize Jarvis to access data from those services according to the scopes you grant during OAuth. That data is fetched on demand by your server and is not relayed through Jarvis Automation infrastructure.

## Information the mobile app collects

The Jarvis Automation mobile app requests the following device permissions, and uses them only for the stated purposes:

| Permission | Purpose |
|------------|---------|
| Camera | Scanning QR codes during node pairing |
| Microphone | Voice input when the in-app assistant is used (optional) |
| Local network | Discovering your Jarvis server and Pi Zero nodes on your Wi-Fi |
| Notifications | Delivering push notifications from your Jarvis server |
| Secure storage (keychain) | Storing authentication tokens for your Jarvis server |

The mobile app does not include any third-party analytics, advertising, crash reporting, or tracking SDKs. The app sends network requests only to:

- Your own Jarvis server (the host you configured)
- Jarvis Automation cloud services that you have explicitly opted into (Pantry package store)
- Third-party OAuth providers (Google, etc.) only when you initiate an OAuth flow

## Information our cloud services collect

If you choose to use a Jarvis Automation cloud service, the following data is sent to and stored on our infrastructure:

**Jarvis Pantry (package store).** When you browse, install, or share community packages, we receive your account identifier and the package identifiers you interact with. We store the packages themselves (which you publish) and download counts.

**App Store and Google Play.** When you download the Jarvis Automation mobile app, Apple and Google may collect installation and usage telemetry according to their respective privacy policies. We do not receive personally identifying information from these stores beyond aggregate install counts.

We do not operate any other cloud services that receive your data by default.

## How we use information

We use the limited cloud-collected information described above to:

- Operate the Pantry package store and let you share installable packages with other users
- Deliver mobile app updates through Apple App Store and Google Play
- Respond to your direct support requests if you contact us

We do not use your information for advertising, profiling, or sale to third parties.

## How we share information

We do not sell or rent your personal information. We share data only in these circumstances:

- **With your consent**, when you enroll OAuth providers or share Pantry packages publicly.
- **With infrastructure providers** that host our cloud services (currently Cloudflare and Fly.io), under contracts that prohibit them from using the data for their own purposes.
- **When required by law**, in response to a valid legal process. We will notify you unless the request prohibits notification.

## Data retention and deletion

**Deleting your account.** You can permanently delete your Jarvis account from within the mobile app: open **Settings → Account → Delete Account**, re-enter your password, and type DELETE to confirm. Deletion is immediate and cannot be undone.

Deleting your account permanently removes the following from your Jarvis server:

- Your account identity (email and password hash) and all active sign-in sessions
- Voice transcripts, assistant replies, and personal memories associated with your account
- Your personal settings and any connected-service (OAuth) tokens stored for you
- Your push-notification device tokens and notification inbox
- Any household for which you are the only member, including that household's node registrations and invites

To avoid disrupting other people who share your setup, you cannot delete your account while voice nodes are still registered to it, or while you are the only administrator of a household that has other members. Remove those nodes, or make another member an administrator, and then delete your account.

**Self-hosted data** is otherwise retained according to your own server's configuration — you control it.

**Cloud-stored data:**

- Pantry account: retained while your account is active. Deleted within 30 days of an account-deletion request.
- Pantry packages you have published: retained while your account is active. You can delete individual packages at any time.
- Mobile app diagnostic logs (if you opt to send them): retained for 30 days.

To delete data held by Jarvis Automation's cloud services (such as the Pantry package store), email <alex@alexberardi.net> from the address on file, or remove your individual packages from within the app.

## Children

Jarvis is not directed at children under 13, and we do not knowingly collect personal information from children under 13. If you believe a child has provided information to a Jarvis cloud service, contact us and we will delete it.

## Security

We use industry-standard practices to secure data on our cloud services, including encryption in transit (TLS) and at rest. Mobile app authentication tokens are stored in the platform's secure keychain. Node-level secrets are stored in an AES-256 encrypted database with a key that never leaves the device.

See [Security](index.md) for a fuller description of the platform's security model.

## Changes to this policy

We may update this privacy policy from time to time. Material changes will be announced through the mobile app and on this page. The "Last updated" date at the top of this policy reflects the most recent revision.

## Contact

For privacy questions or data deletion requests:

**Email:** <alex@alexberardi.net>

We aim to respond within 30 days.
