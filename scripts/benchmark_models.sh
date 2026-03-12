#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# AARI-NEXUS Model Benchmark Script
# Compares SLMs on latency, tokens/sec, and response quality
#
# Usage:
#   bash scripts/benchmark_models.sh
#   bash scripts/benchmark_models.sh --prompt "custom prompt here"
# ──────────────────────────────────────────────────────────────

set -euo pipefail

# ── Config ────────────────────────────────────────────────────
MODELS=("phi3:mini" "qwen2.5:3b" "gemma2:2b")
LOG_DIR="./logs"
LOG_FILE="$LOG_DIR/benchmark_$(date +%Y%m%d_%H%M%S).txt"
OLLAMA_API="http://localhost:11434/api/generate"

mkdir -p "$LOG_DIR"

# ── Default benchmark prompt ──────────────────────────────────
PROMPT="${1:-Summarize this document and extract 5 key action items: AARI-NEXUS is a local AI knowledge and reasoning system designed to teach AI infrastructure. It uses small language models, vector stores, and domain routing to answer questions about quantum computing, robotics, and AI systems.}"

# ── Colors ────────────────────────────────────────────────────
BOLD=$(tput bold 2>/dev/null || echo "")
RESET=$(tput sgr0 2>/dev/null || echo "")
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ── Header ────────────────────────────────────────────────────
print_header() {
  echo ""
  echo "${BOLD}══════════════════════════════════════════════════${RESET}"
  echo "${BOLD}     AARI-NEXUS Model Benchmark                   ${RESET}"
  echo "${BOLD}══════════════════════════════════════════════════${RESET}"
  echo "  Date   : $(date)"
  echo "  Models : ${MODELS[*]}"
  echo "  Prompt : ${PROMPT:0:80}..."
  echo "${BOLD}══════════════════════════════════════════════════${RESET}"
  echo ""
}

# ── Single model benchmark ────────────────────────────────────
benchmark_model() {
  local model="$1"
  echo -e "${CYAN}── Model: $model ──${NC}"

  # Check model is available
  if ! ollama list | grep -q "${model%%:*}"; then
    echo -e "${YELLOW}  Pulling $model...${NC}"
    ollama pull "$model"
  fi

  # Time the generation
  local start end elapsed tokens_est tps

  start=$(date +%s%N)

  RESPONSE=$(curl -s "$OLLAMA_API" \
    -H "Content-Type: application/json" \
    -d "{
      \"model\": \"$model\",
      \"prompt\": \"$PROMPT\",
      \"stream\": false
    }")

  end=$(date +%s%N)
  elapsed=$(( (end - start) / 1000000 ))  # ms

  # Parse response
  ANSWER=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('response','ERROR')[:400])" 2>/dev/null || echo "parse error")
  tokens_est=$(echo "$ANSWER" | wc -w | tr -d ' ')
  elapsed_sec=$(echo "scale=2; $elapsed / 1000" | bc)
  tps=$(echo "scale=1; $tokens_est / ($elapsed / 1000)" | bc 2>/dev/null || echo "n/a")

  echo -e "  ${GREEN}Latency   : ${elapsed_sec}s${NC}"
  echo -e "  ${GREEN}~Tokens   : ${tokens_est} words${NC}"
  echo -e "  ${GREEN}~T/s      : ${tps} words/sec${NC}"
  echo "  Response preview:"
  echo "  ─────────────────────────────────────"
  echo "$ANSWER" | fold -w 70 | head -8 | sed 's/^/  /'
  echo "  ─────────────────────────────────────"
  echo ""

  # Log results
  {
    echo "MODEL: $model"
    echo "LATENCY_MS: $elapsed"
    echo "TOKENS_EST: $tokens_est"
    echo "TPS: $tps"
    echo "RESPONSE: $ANSWER"
    echo "---"
  } >> "$LOG_FILE"
}

# ── Summary table ─────────────────────────────────────────────
print_summary() {
  echo "${BOLD}══════════════════════════════════════════════════${RESET}"
  echo "${BOLD}  Benchmark Summary${RESET}"
  echo "${BOLD}══════════════════════════════════════════════════${RESET}"
  printf "  %-25s %-12s %-12s\n" "Model" "Latency" "~Words/sec"
  printf "  %-25s %-12s %-12s\n" "─────────────────────────" "──────────" "──────────"

  while IFS= read -r line; do
    if [[ "$line" =~ ^MODEL:\ (.+)$ ]]; then model="${BASH_REMATCH[1]}"; fi
    if [[ "$line" =~ ^LATENCY_MS:\ (.+)$ ]]; then lat="${BASH_REMATCH[1]}"; fi
    if [[ "$line" =~ ^TPS:\ (.+)$ ]]; then
      tps="${BASH_REMATCH[1]}"
      lat_s=$(echo "scale=2; $lat / 1000" | bc)
      printf "  %-25s %-12s %-12s\n" "$model" "${lat_s}s" "$tps"
    fi
  done < "$LOG_FILE"

  echo "${BOLD}══════════════════════════════════════════════════${RESET}"
  echo "  Full log: $LOG_FILE"
  echo ""
}

# ── Main ──────────────────────────────────────────────────────
# Ensure Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
  echo "Starting Ollama..."
  ollama serve &>/dev/null &
  sleep 3
fi

print_header

for model in "${MODELS[@]}"; do
  benchmark_model "$model"
done

print_summary
