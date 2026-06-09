# Pantry Callback Signing Key Rotation

The `PANTRY_CALLBACK_SIGNING_KEY` is shared between the Pantry Store (Fly.io) and the GitHub Actions runner (`jarvis-pantry-runner`). Both must be updated together.

## Steps

1. **Generate a new key**

   ```bash
   openssl rand -hex 32
   ```

2. **Update the Fly secret** (pantry store server)

   ```bash
   fly secrets set PANTRY_CALLBACK_SIGNING_KEY=<new-key> -a jarvis-pantry-store
   ```

   Fly restarts the app automatically. The old key stops being accepted immediately after the restart completes.

3. **Update the GHA environment secret** (runner side)

   In `alexberardi/jarvis-pantry-runner` → **Settings → Environments → `pantry-callback` → Secrets**, update `PANTRY_CALLBACK_SIGNING_KEY` to the new value.

4. **Verify**

   Submit a test command through the Pantry web UI and confirm it reaches `published` state. A 401 response on the callback endpoint means the keys are still mismatched.

## Impact Window

From the moment the Fly secret is updated until the GHA secret is updated, any `workflow_dispatch` runs that started with the old nonce/key pair will 401 on callback. The pantry callback-timeout watcher retries stalled submissions, so these will eventually resolve once both sides are in sync — but submissions in-flight during the window may be delayed up to the timeout interval (~10 min default).

**Minimize the window**: update the GHA secret immediately after the Fly deploy confirms healthy (`/health` returns 200).
