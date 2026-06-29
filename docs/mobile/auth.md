# Authentication

## Landing Screen

The landing screen appears when you're not logged in. Tap **Create Account** to register or **Sign In** to log in.

## Registration

Tap **Create Account** to register. Provide an email, username, and password. A default household ("My Home") is created automatically.

### Invite Codes

If you have an invite code from an existing household, enter it during registration to join that household directly instead of creating a new one.

## Login

Enter your email and password. After login, the app loads your households and connects to the command center.

### Biometric Login (Face ID / Touch ID)

On devices with Face ID, Touch ID, or Android biometrics enrolled, the Login screen shows a **"Use Face ID / Touch ID next time"** checkbox below the login form. Check it before tapping **Log In** to opt in to biometric session restore.

After enrolling, the app rewrites your refresh token in the OS keychain with biometric access control (`requireAuthentication`). Future cold-boot launches show the OS biometric prompt instead of the password form.

- If the prompt is **cancelled or fails**, an **"Unlock with Face ID / Touch ID"** retry button appears on the login screen. Email + password is always available as a fallback.
- The checkbox only appears when the device has strong biometrics enrolled. On Android this additionally requires an app build that includes the `USE_BIOMETRIC` permission.
- To toggle biometric login after enrolment, go to **Settings → Security**.

## Multi-Household

Users can belong to multiple households. Switch between them in **Settings > Household**.

### Roles

| Role | Permissions |
|------|-------------|
| **Member** | Chat, view devices, run routines |
| **Power User** | + Create invite codes, register nodes |
| **Admin** | + Manage members, edit household, kick members |
