# ReClaw Scaffold

A minimal, clone-and-run starter kit for building a personal AI agent that lives in your Discord server.

Built on the ReClaw architecture: flat-file memory, heartbeat scheduling, persona routing, and overnight self-optimization — no cloud required.

---

## Prerequisites (5 min)

Before you start, make sure you have:

- **WSL2 + Ubuntu** (or any Linux — macOS also works)
- **Python 3.10+** (`python3 --version` to check)
- **A Discord server** you administrate
- **Claude Max subscription** (for the Claude Code SDK proxy — no API key needed)
- **Claude Code CLI** installed (`npm install -g @anthropic-ai/claude-code`)

Optional but recommended:
- A Perplexity API key (enables web search in the daily brief and heartbeat)

---

## 30-Minute Quick Start

### Step 1 — Clone and setup (2 min)

```bash
git clone https://github.com/sch9826/reclaw-scaffold.git
cd reclaw-scaffold
chmod +x setup.sh
./setup.sh
```

The setup script creates a virtual environment, installs dependencies, copies template files to `workspace/`, and runs a dry-run check.

### Step 2 — Create a Discord bot (5 min)

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. Click **New Application**, give it a name
3. Go to **Bot** → **Add Bot** → copy the **Token** (you'll need this for `.env`)
4. Under **Privileged Gateway Intents**, enable **Message Content Intent**
5. Go to **OAuth2 → URL Generator**:
   - Scopes: `bot`
   - Bot Permissions: `Send Messages`, `Read Message History`, `View Channels`
6. Copy the generated URL, open it in your browser, and add the bot to your server

### Step 3 — Configure .env (2 min)

```bash
# .env was already created by setup.sh
nano .env   # or use any editor
```

Required fields:
```bash
DISCORD_BOT_TOKEN=your-bot-token-here
DISCORD_GUILD_ID=your-server-id-here
```

To get your server ID: enable **Developer Mode** in Discord (Settings → Advanced → Developer Mode), then right-click your server and click **Copy Server ID**.

### Step 4 — Edit USER.md (15 min — don't skip this)

```bash
nano workspace/USER.md
```

This is the most important step. The agent loads USER.md into every conversation. The more you fill in, the more useful the agent becomes.

At minimum, fill in:
- Your name and location
- Your main projects or businesses
- How you prefer to communicate
- What you expect from the agent

Also edit `workspace/SOUL.md` to give your agent a name and voice.

### Step 5 — Start the Claude Code proxy

In a separate terminal:
```bash
claude --serve --port 3456
```

This starts a local OpenAI-compatible proxy using your Claude Max subscription. No API key needed.

### Step 6 — Start the agent (1 min)

```bash
source venv/bin/activate
python src/main.py
```

You should see:
```
[INFO] main: Bot connected as YourAgent#1234 (id=...)
[INFO] heartbeat: HEARTBEAT_OK
```

Say hello in your Discord server. The bot should respond.

### Step 7 — Install as a systemd service (2 min)

To run the agent continuously and survive reboots:

```bash
# Edit the service file to set your working directory
nano systemd/openclaw.service   # update WorkingDirectory and ExecStart paths

sudo cp systemd/openclaw.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now openclaw
```

For overnight autoresearch (optional):
```bash
sudo cp systemd/reclaw-autoresearch.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now reclaw-autoresearch.timer
```

### Step 8 — Verify heartbeat (5 min wait)

After 30 minutes, check the heartbeat log:
```bash
cat workspace/memory/heartbeat.log
```

You should see lines like:
```
[2026-04-12 02:30:00] HEARTBEAT_OK — no open tasks, no flagged items
```

HEARTBEAT_OK means the agent is alive and found nothing urgent.

---

## Project Structure

```
reclaw-scaffold/
├── src/
│   ├── main.py              — Service entry point
│   ├── agent.py             — Core reasoning loop
│   ├── heartbeat.py         — Proactive alert system
│   ├── memory.py            — Flat-file memory read/write/search
│   └── persona_router.py    — Channel → persona mapping
├── workspace/
│   ├── memory/              — All memory files live here
│   ├── souls/               — Per-persona soul files (optional)
│   ├── skills/daily-brief/  — Example skill
│   └── autoresearch/        — Overnight self-optimization loop
├── systemd/                 — Service and timer files
├── templates/               — SOUL.md, USER.md, AGENTS.md, DIRECTIVE.md
├── .env.example             — All env vars with comments
├── requirements.txt
└── setup.sh
```

---

## How It Works

### Message Flow
1. Discord message arrives → `main.py` routes it to `agent.py`
2. `agent.py` looks up the persona for that channel (`persona_router.py`)
3. Agent loads SOUL.md + USER.md + AGENTS.md as system context
4. Agent searches memory for relevant background (`memory.py`)
5. Agent calls Claude via local proxy and returns a response
6. If the response is long (> 200 chars), a snippet is saved to memory

### Memory
All memory is flat Markdown files in `workspace/memory/`. No vector database. Search is keyword-based — simple and zero-dependency. This is intentional: you can read, edit, and version-control your agent's memory directly.

### Heartbeat
Every 30 minutes, the heartbeat checks `workspace/memory/tasks.md` for open items (`- [ ]` lines). If nothing is found, it logs `HEARTBEAT_OK` and stays quiet. If tasks or flagged items exist, it sends a Discord message to `DISCORD_HEARTBEAT_CHANNEL`.

### Persona Routing
`workspace/persona_routing.json` maps Discord channel IDs to persona names. Each persona can optionally have its own soul file at `workspace/souls/<persona-name>.md`. If no mapping exists, all channels use the default "assistant" persona.

---

## Adding Skills

Skills are Markdown files at `workspace/skills/<skill-name>/SKILL.md`. Each skill defines:
- **Triggers** — phrases that activate the skill
- **Prompt template** — how to format the request to the LLM
- **Tools** — which memory or API calls to make

See `workspace/skills/daily-brief/SKILL.md` for a working example.

To wire a skill, add a routing rule in `workspace/AGENTS.md`.

---

## Overnight Autoresearch

The autoresearch loop (`workspace/autoresearch/`) runs test cases through your agent every night, scores the responses using an LLM-as-judge, and writes a report to `workspace/autoresearch/logs/`.

To run it manually:
```bash
source venv/bin/activate
python workspace/autoresearch/orchestrator.py
```

Add your own test cases to `workspace/autoresearch/test_cases/general.json`.

---

## Troubleshooting

**Bot doesn't respond:**
- Check `DISCORD_BOT_TOKEN` is correct in `.env`
- Verify Message Content Intent is enabled in the Discord developer portal
- Make sure the bot has permission to read and send messages in the channel

**"Could not reach model proxy" error:**
- Is `claude --serve --port 3456` running?
- Check `OPENCLAW_PROXY_URL` in `.env` matches the port

**Heartbeat never fires:**
- The scheduler runs in a background thread — check the console for `[INFO] heartbeat.py: HEARTBEAT_OK`
- If using systemd, check: `journalctl -u openclaw -f`

**Memory not persisting:**
- Verify the `workspace/memory/` directory exists and is writable
- Check logs for "Could not save to memory" warnings

---

## What to Build Next

This scaffold is the foundation. The full guide covers:
- Mission Control dashboard (multi-agent orchestration)
- Board meeting system (structured decision reviews)
- X/Twitter integration (posting and monitoring)
- Email drafting and inbox triage
- Multi-persona channel strategy
- Advanced autoresearch with prompt optimization

---

## License

MIT License — use this however you want.
