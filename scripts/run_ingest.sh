#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# AARI-NEXUS Ingestion Runner
# Syncs all data/ domain folders into PrivateGPT vector store
#
# Usage:
#   bash scripts/run_ingest.sh              # ingest all domains
#   bash scripts/run_ingest.sh quantum      # ingest one domain
# ──────────────────────────────────────────────────────────────

set -euo pipefail

NEXUS_ROOT="$HOME/aari-nexus"
PGPT_ROOT="$HOME/private-gpt"
DATA_DIR="$NEXUS_ROOT/data"
LOG_DIR="$NEXUS_ROOT/logs"
LOG_FILE="$LOG_DIR/ingest_$(date +%Y%m%d_%H%M%S).log"

DOMAINS=("quantum" "robotics" "infrastructure" "world_models" "linear_algebra" "research_papers" "google_drive")
BOLD=$(tput bold 2>/dev/null || echo "")
RESET=$(tput sgr0 2>/dev/null || echo "")
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

mkdir -p "$LOG_DIR"

# ── Preflight checks ──────────────────────────────────────────
check_ollama() {
  if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${YELLOW}Starting Ollama...${NC}"
    ollama serve &>/dev/null &
    sleep 3
  fi
  echo -e "${GREEN}✓ Ollama running${NC}"
}

check_pgpt() {
  if [[ ! -d "$PGPT_ROOT" ]]; then
    echo -e "${RED}✗ PrivateGPT not found at $PGPT_ROOT${NC}"
    echo "  Run the setup first: see README.md"
    exit 1
  fi
  echo -e "${GREEN}✓ PrivateGPT found${NC}"
}

# ── Ingest one domain folder ──────────────────────────────────
ingest_domain() {
  local domain="$1"
  local domain_path="$DATA_DIR/$domain"

  if [[ ! -d "$domain_path" ]]; then
    echo -e "  ${YELLOW}SKIP${NC} $domain/ — folder not found"
    return
  fi

  # Count files
  local file_count
  file_count=$(find "$domain_path" -type f \
    \( -name "*.pdf" -o -name "*.md" -o -name "*.txt" \
       -o -name "*.docx" -o -name "*.rst" \) | wc -l | tr -d ' ')

  if [[ "$file_count" -eq 0 ]]; then
    echo -e "  ${YELLOW}SKIP${NC} $domain/ — no documents yet"
    return
  fi

  echo -e "  ${CYAN}Ingesting${NC} $domain/ ($file_count file(s))..."

  # Enable local ingestion flag in settings
  local settings_backup="$PGPT_ROOT/settings.yaml.bak"
  cp "$PGPT_ROOT/settings.yaml" "$settings_backup"

  # Temporarily enable local ingestion via sed
  sed -i.bak2 's/enabled: ${LOCAL_INGESTION_ENABLED:false}/enabled: true/' "$PGPT_ROOT/settings.yaml" || true

  # Run PrivateGPT ingest
  cd "$PGPT_ROOT"
  PGPT_PROFILES=ollama python3 -m poetry run python scripts/ingest_folder.py \
    "$domain_path" \
    --log-file "$LOG_FILE" 2>&1 | grep -E "(Ingesting|Completed|Failed|Error)" | sed "s/^/    /" || true

  # Restore settings
  cp "$settings_backup" "$PGPT_ROOT/settings.yaml"
  rm -f "$settings_backup" "$PGPT_ROOT/settings.yaml.bak2"

  echo -e "  ${GREEN}✓${NC} $domain/ ingested"
}

# ── Header ────────────────────────────────────────────────────
echo ""
echo "${BOLD}══════════════════════════════════════════════════${RESET}"
echo "${BOLD}     AARI-NEXUS Ingestion Pipeline                ${RESET}"
echo "${BOLD}══════════════════════════════════════════════════${RESET}"
echo "  Date    : $(date)"
echo "  Data    : $DATA_DIR"
echo "  Log     : $LOG_FILE"
echo "${BOLD}══════════════════════════════════════════════════${RESET}"
echo ""

check_ollama
check_pgpt
echo ""

# ── Run ingestion ─────────────────────────────────────────────
if [[ "${1:-}" != "" ]]; then
  # Single domain
  echo "Ingesting domain: $1"
  ingest_domain "$1"
else
  # All domains
  for domain in "${DOMAINS[@]}"; do
    ingest_domain "$domain"
  done
fi

echo ""
echo "${BOLD}══════════════════════════════════════════════════${RESET}"
echo -e "${GREEN}  Ingestion complete.${RESET}"
echo "  Log: $LOG_FILE"
echo ""
echo "  To verify in NEXUS:"
echo "    python3 $NEXUS_ROOT/scripts/nexus_query.py 'Explain the lithium battery VQE setup'"
echo "${BOLD}══════════════════════════════════════════════════${RESET}"
echo ""
