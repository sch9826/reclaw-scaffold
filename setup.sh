#!/bin/bash
# setup.sh — One-command setup for ReClaw Scaffold.
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
#
# What this does:
#   1. Creates a Python virtual environment in ./venv
#   2. Installs all dependencies from requirements.txt
#   3. Copies .env.example → .env (if .env doesn't already exist)
#   4. Copies template files to workspace/ (if targets don't already exist)
#
# After running:
#   1. Edit .env — add your DISCORD_BOT_TOKEN and DISCORD_GUILD_ID
#   2. Edit workspace/USER.md — fill in your identity (this is critical)
#   3. Edit workspace/SOUL.md — give your agent a name and voice
#   4. Run: source venv/bin/activate && python src/main.py --dry-run
#   5. If dry-run passes, start for real: python src/main.py

set -e  # exit on error

echo "==> ReClaw Scaffold Setup"
echo ""

# ── Python version check ───────────────────────────────────────────────────────
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED="3.10"
if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"; then
    echo "[OK] Python $PYTHON_VERSION found"
else
    echo "[ERROR] Python 3.10+ required (found $PYTHON_VERSION)"
    exit 1
fi

# ── Virtual environment ────────────────────────────────────────────────────────
if [ -d "venv" ]; then
    echo "[SKIP] venv already exists"
else
    echo "==> Creating virtual environment..."
    python3 -m venv venv
    echo "[OK] Virtual environment created at ./venv"
fi

# ── Activate and install ───────────────────────────────────────────────────────
echo "==> Installing dependencies..."
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "[OK] Dependencies installed"

# ── Copy .env ─────────────────────────────────────────────────────────────────
if [ -f ".env" ]; then
    echo "[SKIP] .env already exists — not overwriting"
else
    cp .env.example .env
    echo "[OK] .env created from .env.example"
fi

# ── Copy templates to workspace/ ──────────────────────────────────────────────
mkdir -p workspace workspace/memory workspace/souls workspace/skills

for template in SOUL.md USER.md AGENTS.md DIRECTIVE.md; do
    dest="workspace/$template"
    if [ -f "$dest" ]; then
        echo "[SKIP] $dest already exists — not overwriting"
    else
        cp "templates/$template" "$dest"
        echo "[OK] $dest created from templates/$template"
    fi
done

# ── Create persona_routing.json if missing ────────────────────────────────────
if [ -f "workspace/persona_routing.json" ]; then
    echo "[SKIP] workspace/persona_routing.json already exists"
else
    cat > workspace/persona_routing.json <<'EOF'
{
  "CHANNEL_ID_HERE": "assistant",
  "_comment": "Replace CHANNEL_ID_HERE with your Discord channel ID. Add more entries as needed."
}
EOF
    echo "[OK] workspace/persona_routing.json created (placeholder)"
fi

# ── Dry-run check ──────────────────────────────────────────────────────────────
echo ""
echo "==> Running dry-run check (python src/main.py --dry-run)..."
if python src/main.py --dry-run; then
    echo "[OK] Dry-run passed"
else
    echo "[WARN] Dry-run failed — check .env and workspace/ files before starting"
fi

echo ""
echo "========================================"
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env            — add DISCORD_BOT_TOKEN"
echo "  2. Edit workspace/USER.md  — fill in your identity"
echo "  3. Edit workspace/SOUL.md  — name and voice for your agent"
echo "  4. Start the agent:"
echo "     source venv/bin/activate"
echo "     python src/main.py"
echo "========================================"
