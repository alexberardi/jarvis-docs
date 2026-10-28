# Privacy Policy

**Last updated:** October 28, 2026

This privacy policy describes how Jarvis Automation ("we", "us", "Jarvis") handles information collected through the Jarvis platform, including the **Jarvis Automation** mobile app, the **Jarvis desktop agent** and the **Jarvis Browser Control** browser extension, the self-hosted **Jarvis Automation server** (one program, `jarvisd`, that you run on your own hardware), and optional cloud services.

Jarvis is **self-hosted by default**. Most data flows in Jarvis never reach servers operated by us — they stay on hardware you own and operate. This policy distinguishes between the two cases.

## Summary

| Data | Where it goes | When |
|------|---------------|------|
| Voice recordings | Your own Jarvis Automation server (speech to text) | Always |
| Voice transcripts and assistant replies | Your own Jarvis Automation server | Always |
| Account credentials (email, password hash) | Your own Jarvis Automation server | Always |
| Authentication tokens on the mobile app | Encrypted in your device's OS keychain | Always |
| Pantry package metadata | Jarvis Automation cloud (Pantry service) | Only when you use the package store |
| Push notification titles and bodies, and device push tokens | Jarvis Automation cloud (push relay), then Expo, Apple and Google | Only when push notifications are turned on |
| Google account data (Calendar, Drive, Gmail, Nest) | Google, then your own server | Only when you enroll OAuth |
| Local network scan results (Wi-Fi SSIDs, device IPs) | Your device only | During node provisioning |
| Camera images (QR codes) | Your device only (transient) | During node pairing |
| Browser tab titles and URLs (Browser Control extension) | Your own server, via the desktop agent on your computer | Only when you ask Jarvis to do something with your tabs |
| Visible page text (Browser Control extension) | Your own server, via the desktop agent on your computer | Only when you ask Jarvis to read or act on a page |
| Screen captures (desktop agent, "read the screen") | Your own server | Only when you ask Jarvis to read your screen |

We do not sell your data. We do not run analytics on the mobile app, the desktop agent, the browser extension or the self-hosted backend.

## Information you provide

**Account information.** When you create a Jarvis account, you provide an email address and password. These are stored on your Jarvis Automation server. If you are self-hosting, this is your own server. If you are using a managed Jarvis instance, this is the host you connect the mobile app to.

**Voice input.** Voice commands you speak to a Jarvis node are recorded, transcribed and processed by your Jarvis Automation server. All of this runs on the server you have configured, unless you configure a cloud language-model provider, which then receives your conversations.

**Configuration data.** Node names, room assignments, device pairings, routines, and similar settings are stored on your own server.

**Optional integrations.** If you enroll third-party services (Google Calendar, Gmail, Drive, Nest, Home Assistant, etc.), you authorize Jarvis to access data from those services according to the scopes you grant during OAuth. That data is fetched on demand by your server or your node and is not relayed through Jarvis Automation infrastructure. If your server's operator sets an OAuth relay (`oauth.relay_url`, empty by default), the provider's sign-in redirect, which carries a one-time authorization code, passes through that relay on its way back to the app.

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
- Expo, to get a device push token, only when you turn on push notifications in the app's Settings
- Third-party OAuth providers (Google, etc.) only when you initiate an OAuth flow

## Information the desktop agent and browser extension handle

The **Jarvis desktop agent** runs on your computer and connects only to the Jarvis server you
configured. It acts on your computer (opening apps, managing windows, reading the screen) only
when you ask Jarvis to. Screen captures are sent to your own server for that one request and
are not kept by the agent.

The **Jarvis Browser Control** extension (Chrome, Firefox and other Chromium browsers) lets
Jarvis work with your browser tabs. It:

- **Communicates only with the Jarvis desktop agent on the same computer**, through the
  browser's native-messaging channel. It makes no network requests of its own. Web pages and
  other extensions cannot send it anything.
- **Reads tab titles and URLs** when you ask Jarvis to list, open, switch or close tabs.
- **Reads a page's visible text** when you ask Jarvis to read or summarise a page.
- **Fills in a field or clicks a button** only when you ask Jarvis to, and only when exactly one
  field or button on the page matches what you said. It writes the text you dictated and never
  reads a field back. A password field is filled only when you say it is the password field.
- **Runs errands you give Jarvis** in a browser window it opens behind yours: it lists that
  page's buttons, links and form fields, with what ordinary fields already contain (such as an
  email or address, so Jarvis doesn't type them twice), acts on them, takes a picture of that
  window when the list isn't enough, and saves a file the errand needs (such as a statement) to
  your downloads folder. Password, card, one-time-code and hidden fields are listed without
  their contents, and it never types into a password field this way. It never opens, moves or
  deletes files, and never reads your other downloads.
- **Never reads passwords, card numbers or one-time codes.**
- **Controls audio and video** on a page (play, pause, seek) when you ask it to.
- **Stores nothing.** It keeps no history, cookies, browsing data or settings.

This data goes from the extension to the desktop agent, then to **your own Jarvis server**, and
is used only to carry out your request. It never reaches Jarvis Automation or any third party.
It is not sold, not used for advertising, profiling or creditworthiness, and not used for any
purpose unrelated to the feature you invoked. What your server keeps (for example, the
conversation transcript) follows your server's own retention settings.

## Information our cloud services collect

If you choose to use a Jarvis Automation cloud service, the following data is sent to and stored on our infrastructure:

**Jarvis Pantry (package store).** When you or your server browse or install packages, the Pantry receives the package names requested and the requesting IP address, which it uses for rate limiting; these requests carry no account identifier. Each install adds to that package's public install count. When you publish or share a package, we receive your Pantry account identifier and store the packages you publish.

**Push relay (optional).** Phone push notifications are off until your server's operator turns them on (the "Phone push notifications" switch in the setup wizard's privacy step, or the `relay.url` setting). When they are on, your server sends each notification to the relay it is set to use; the default is ours, `relay.jarvisautomation.io`. For each notification the relay receives the title and the body, any data attached to it, the push tokens of the devices to deliver it to, and your household's identifier. The relay forwards the notification to Expo's push service, which delivers it through Apple (APNs) or Google (FCM). The relay keeps no database: it does not store titles, bodies or push tokens, and holds only short-lived rate-limit counters in memory. Its logs record your household's identifier and IP address when your server registers with it. Expo, Apple and Google handle the notifications under their own privacy policies. To get a push token, the mobile app also contacts Expo when you turn push notifications on.

**App Store and Google Play.** When you download the Jarvis Automation mobile app, Apple and Google may collect installation and usage telemetry according to their respective privacy policies. We do not receive personally identifying information from these stores beyond aggregate install counts.

We do not operate any other cloud services that receive your data. Neither the Pantry nor the push relay receives anything until you turn it on.

## How we use information

We use the limited cloud-collected information described above to:

- Operate the Pantry package store and let you share installable packages with other users
- Deliver your push notifications, if you turn them on
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
- Push relay: notifications pass through and are not stored. Rate-limit counters are kept in memory only and reset when the relay restarts.
- Mobile app diagnostic logs (if you opt to send them): retained for 30 days.

To delete data held by Jarvis Automation's cloud services (such as the Pantry package store), email <admin@jarvisautomation.io> from the address on file, or remove your individual packages from within the app.

## Children

Jarvis is not directed at children under 13, and we do not knowingly collect personal information from children under 13. If you believe a child has provided information to a Jarvis cloud service, contact us and we will delete it.

## Security

We use industry-standard practices to secure data on our cloud services, including encryption in transit (TLS) and at rest. Mobile app authentication tokens are stored in the platform's secure keychain.

Secrets for your commands (API keys and account tokens) are encrypted between the mobile app and the node with the node's own key. Your Jarvis Automation server stores and passes on only the encrypted form. On a Raspberry Pi running the Python node software, they are stored in an AES-256 encrypted database (SQLCipher). On a computer with the desktop agent, they are stored, with the node's key, in files only your user account can read (0600), not encrypted. For the desktop agent, and for a node that gets its key without its setup hotspot, the key itself passes once through your server's memory when it is delivered.

Your Jarvis Automation server keeps its data, including any API keys you give it for cloud model providers, phone calls (Twilio) or Hugging Face, in a database in its data directory that only the server's user account can read. This database and its backups are not encrypted at rest.

See [Security](index.md) for a fuller description of the platform's security model.

## Changes to this policy

We may update this privacy policy from time to time. Material changes will be announced through the mobile app and on this page. The "Last updated" date at the top of this policy reflects the most recent revision.

## Contact

For privacy questions or data deletion requests:

**Email:** <admin@jarvisautomation.io>

We aim to respond within 30 days.
