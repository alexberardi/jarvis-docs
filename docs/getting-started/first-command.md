# Your First Command

You have finished the setup wizard and services are starting. This page walks you through verifying everything works and sending your first command.

## 1. Verify Services Are Running

### Via the Admin Dashboard

Open [http://localhost:7711/dashboard](http://localhost:7711/dashboard) in your browser. The Dashboard page shows every container's status. All core services should show a green "running" status.

### Via the Command Line

Check container status with Docker Compose:

```bash
cd ~/.jarvis/compose && docker compose ps
```

You should see containers for at least: `jarvis-postgres`, `jarvis-config-service`, `jarvis-auth`, `jarvis-command-center`, and `jarvis-llm-proxy`.

## 2. Health Check Cheat Sheet

Hit each service's health endpoint to confirm it is responding:

| Service | Command | Expected |
|---------|---------|----------|
| Config Service | `curl -s http://localhost:7700/health` | `{"status":"ok"}` |
| Auth | `curl -s http://localhost:7701/health` | `{"status":"ok"}` |
| Command Center | `curl -s http://localhost:7703/health` | `{"status":"ok"}` |
| LLM Proxy | `curl -s http://localhost:7704/health` | `{"status":"ok"}` |
| TTS | `curl -s http://localhost:7707/health` | `{"status":"ok"}` |
| Logs | `curl -s http://localhost:7702/health` | `{"status":"ok"}` |

!!! tip
    The LLM Proxy can take up to two minutes to load the model. If it returns an error, wait and try again.

If any service is not responding, check its logs:

```bash
cd ~/.jarvis/compose && docker compose logs <service-name> --tail 50
```

See the [Troubleshooting](../troubleshooting/index.md) guide for common fixes.

## 3. Register a Test Node

Nodes authenticate to the command center with an API key. Register a dev node so you can send test commands.

### Find your admin API key

The admin API key was generated during installation. Find it in the compose environment file:

```bash
grep ADMIN_API_KEY ~/.jarvis/compose/.env
```

Save the value -- you will need it in the next command.

### Register the node

```bash
cd jarvis-node-setup

# List existing households (the installer creates one for your superuser account)
python utils/authorize_node.py --cc-key <ADMIN_API_KEY> --list

# Register a dev node in your household
python utils/authorize_node.py \
  --cc-key <ADMIN_API_KEY> \
  --household-id <household-uuid> \
  --room office \
  --name dev-test \
  --update-config config.json
```

Replace `<ADMIN_API_KEY>` with the value from the previous step, and `<household-uuid>` with the household ID from the `--list` output.

!!! note "Source installs only"
    The `authorize_node.py` script is in the `jarvis-node-setup` directory, which is only available if you cloned the repository. If you installed via Docker or the one-line installer, skip to [Try the Web Chat](#5-try-the-web-chat) instead.

## 4. Send Your First Command

Extract the node credentials from the config file, then send a text command:

```bash
# Extract credentials
NODE_ID=$(python3 -c "import json; print(json.load(open('config.json'))['node_id'])")
API_KEY=$(python3 -c "import json; print(json.load(open('config.json'))['api_key'])")

# Send a command
curl -s -X POST http://localhost:7703/api/v0/command \
  -H "X-API-Key: ${NODE_ID}:${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"text": "what is 5 plus 3"}'
```

**Expected response:**

```json
{
  "success": true,
  "response": "5 plus 3 equals 8.",
  "command": "calculate"
}
```

The exact response text varies depending on your LLM model, but the result should include the correct answer (8).

### What Happened?

The request flowed through the full voice pipeline:

1. **Command Center** received the text input
2. **LLM Proxy** classified the intent as `calculate` and extracted parameters
3. **Calculator command** executed and returned the result
4. **Command Center** formatted the response

In a real voice interaction, Whisper (speech-to-text) runs before step 1, and TTS (text-to-speech) runs after step 4.

## 5. Try the Web Chat

If you enabled `jarvis-web` during installation, open the web chat interface:

```
http://localhost:7722
```

Log in with the superuser account you created during the setup wizard. Type a message like "what is the capital of France" and press Enter.

The web chat sends commands through the same pipeline as voice nodes, so it is a convenient way to test without setting up audio hardware.

## 6. Set Up Voice (Optional)

To use voice input from a Pi Zero or other device, see:

- [Node Setup](../clients/node-setup.md) -- configure a Pi Zero as a voice node
- [Provisioning](../clients/provisioning.md) -- headless WiFi provisioning for Pi Zero nodes

## 7. Install Command Secrets

Some commands need API keys to work. For example, weather commands need an OpenWeather API key, and email commands need OAuth credentials.

List commands and their required secrets:

```bash
cd jarvis-node-setup

# List all commands and their secrets
python scripts/install_command.py --list

# Install all commands (registers them in the database)
python scripts/install_command.py --all
```

Set a secret:

```bash
python utils/set_secret.py OPENWEATHER_API_KEY <your-key> integration
```

Secrets can also be managed through the mobile app's Settings screen.

## Something Not Working?

- **Service not responding:** Check its health endpoint and logs (see [Health Check Cheat Sheet](#2-health-check-cheat-sheet))
- **401 Unauthorized:** Your API key may be wrong -- re-register the node
- **No response from LLM:** Check that a model is loaded via the admin dashboard Models page
- **Detailed troubleshooting:** See the [Troubleshooting](../troubleshooting/index.md) guide

## Next Steps

- [Configure network modes and service discovery](configuration.md)
- [Build your own command](../commands/tutorial-simple.md)
- [Browse the Pantry for community commands](../mobile/pantry.md)
