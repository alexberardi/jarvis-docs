# Your First Command

Once services are running, you can test the voice pipeline by registering a dev node and sending a text command.

## 1. Register a Dev Node

Nodes authenticate to the command center via `X-API-Key: {node_id}:{api_key}`. Register a dev node:

```bash
cd jarvis-node-setup

# Get the admin API key
grep ADMIN_API_KEY ../jarvis-command-center/.env

# List households (or create one)
python utils/authorize_node.py --cc-key <admin_key> --list

# Register
python utils/authorize_node.py \
  --cc-key <admin_key> \
  --household-id <household-uuid> \
  --room office \
  --name dev-mac \
  --update-config config-mac.json
```

## 2. Send a Test Command

With the node registered, send a text command through the pipeline:

```bash
# Extract credentials from config
NODE_ID=$(python -c "import json; c=json.load(open('config-mac.json')); print(c['node_id'])")
API_KEY=$(python -c "import json; c=json.load(open('config-mac.json')); print(c['api_key'])")

# Send a command
curl -X POST http://localhost:7703/api/v0/command \
  -H "X-API-Key: ${NODE_ID}:${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"text": "what is 5 plus 3"}'
```

You should receive a JSON response with the calculation result.

## 3. Install Command Secrets

Commands that need API keys (weather, email, etc.) require secrets to be configured:

```bash
# List all commands and their required secrets
python scripts/install_command.py --list

# Install all commands (creates DB entries for secrets)
python scripts/install_command.py --all
```

Then set secrets via the mobile app's settings sync, or directly:

```bash
python utils/set_secret.py OPENWEATHER_API_KEY <your-key> integration
```

## What Happened?

The request flowed through the full voice pipeline:

1. **Command Center** received the text input
2. **LLM Proxy** classified the intent as `calculate` and extracted parameters `{num1: 5, num2: 3, operation: "add"}`
3. **Calculator command** executed locally on the node and returned `{result: 8}`
4. **Command Center** formatted the response

In a real voice interaction, Whisper (speech-to-text) runs before step 1, and TTS (text-to-speech) runs after step 4.

## Next Steps

- [Configure network modes and service discovery](configuration.md)
- [Build your own command](../commands/tutorial-simple.md)
