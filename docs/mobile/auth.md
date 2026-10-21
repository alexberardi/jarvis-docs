# Authentication

## Landing Screen

The landing screen appears when you're not logged in. It asks for your server first: tap **Set Server URL** and enter `http://<server>:7700` (see [Connect to your server](../clients/node-mobile.md#connect-to-your-server)). Until you do, it shows "Enter your server URL first." Then tap **Log In** or **Create Account**.

## Registration

Tap **Create Account**. The form asks for:

- **Invite Code (optional)**: a code from a household admin. The app checks it and shows "Invalid or expired invite code" if it is not valid.
- **Email**, **Password** and **Confirm Password**. A password needs at least 8 characters, with an uppercase letter, a lowercase letter and a number.
- **Enable push notifications**: turn it off for a fully private, local-only experience. You can change it later in Settings.

With an invite code, the account joins that household. Without one, the server creates a household called "My Home" with you as its admin, but only while sign-up is open: the first account on a new server, or any account when an admin has turned on open registration (the `auth.open_registration` setting). Once the server has an admin, a sign-up without a code is refused with "Registration is closed: ask a household admin for an invite code".

### Invite Codes

Household admins and power users create invite codes in the household's settings. To join another household later with an existing account, use **Settings → Household → Join Another Household**.

## Login

Enter your email and password and tap **Log In**. After login, the app loads your households and connects to your server.

### Temporary passwords

If an admin set a temporary password for you, the app asks you to choose a new one before you go on: enter the **Temporary Password**, a **New Password** and **Confirm New Password**, then tap **Set Password**. Your other devices are signed out.

### Biometric Login (Face ID / Touch ID)

On devices with Face ID, Touch ID, or Android biometrics enrolled, the Login screen shows a **"Use Face ID / Touch ID next time"** checkbox below the login form (**"Use biometric unlock next time"** on Android). Check it before tapping **Log In** to opt in to biometric session restore.

After enrolling, the app rewrites your refresh token in the OS keychain with biometric access control (`requireAuthentication`). Future cold-boot launches show the OS biometric prompt instead of the password form.

- If the prompt is **cancelled or fails**, an **"Unlock with Face ID / Touch ID"** retry button appears on the login screen. Email + password is always available as a fallback.
- The checkbox only appears when the device has strong biometrics enrolled. On Android this additionally requires an app build that includes the `USE_BIOMETRIC` permission.
- To toggle biometric login after enrolment, go to **Settings → Security**.

## Session Lifetime

After a successful login, the app maintains your session silently:

- The **refresh token** is valid for 30 days by default (an admin can change it with the server's `auth.token.refresh_expire_days` setting). The app renews your access token automatically in the background every 10 minutes and once each time you bring the app to the foreground.
- Renewal calls are **single-flight** — concurrent refresh attempts (background timer, foreground resume, and request interceptor) coalesce into one server call, so the rotated refresh token is never double-spent.
- When a session truly expires or is invalidated server-side, the app detects it on the next refresh and takes you directly to the login screen. You will not see a broken node or device screen behind an expired session.
- **Transient network errors** during refresh do not log you out — the app stays signed in and retries on the next cycle.

## Multi-Household

Users can belong to multiple households. Switch between them in **Settings > Household**.

### Roles

| Role | Permissions |
|------|-------------|
| **Member** | Chat, view devices, run routines |
| **Power User** | + Create invite codes, register nodes, install Pantry packages |
| **Admin** | + Manage members, edit household, kick members |
