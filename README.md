# AARI-NEXUS

**Local AI Knowledge and Experimentation Platform**

> AARI-NEXUS teaches students how modern AI systems actually work — not just what they output.

---

## What It Is

AARI-NEXUS is a local AI knowledge and reasoning system for AI infrastructure education. It lets students query a curated technical knowledge base using small local models, while seeing exactly how the system works under the hood.

**Students move from AI consumers to AI operators.**

---

## Architecture

```
User Query
     ↓
Domain Router  →  [quantum | robotics | infrastructure | world_models | linear_algebra | research_papers]
     ↓
Domain Vector Store  (Qdrant, local)
     ↓
SLM Selection  →  [phi3:mini | qwen2.5:3b | gemma2:2b]
     ↓
Response + Trace
```

---

## Trace Output (Teaching Instrument)

Every query shows students the full pipeline:

```
── AARI-NEXUS Trace ──────────────────────────────────
  Domain              : quantum
  Router confidence   : high
  Matched keywords    : qubit, superposition
  Model               : phi3:mini
  Docs retrieved      : 5
  Embedding latency   : 64 ms
  Generation latency  : 1.20 s
──────────────────────────────────────────────────────
```

---

## Models (8 GB RAM Optimized)

| Model | Size | Speed | Use Case |
|---|---|---|---|
| `phi3:mini` | 2.2 GB | Fast | Daily driver, chat, RAG |
| `qwen2.5:3b` | 2.0 GB | Medium | Stronger reasoning |
| `gemma2:2b` | 1.6 GB | Fastest | Lightweight tasks |
| `nomic-embed-text` | 274 MB | — | Document embeddings |

---

## Quick Start

```bash
# 1. Ensure Ollama is running
ollama serve

# 2. Ask a question with full trace
python3 scripts/nexus_query.py "What is a qubit?"

# 3. Ask with a specific model
python3 scripts/nexus_query.py "Explain CUDA memory hierarchy" --model qwen2.5:3b

# 4. Run the model benchmark lab
bash scripts/benchmark_models.sh

# 5. Ingest documents from Google Drive
python3 scripts/ingest_drive.py

# 6. Watch for new documents automatically
python3 scripts/ingest_drive.py --watch
```

---

## Project Structure

```
aari-nexus/
├── config/
│   └── settings.yaml          # Core system config
├── data/
│   ├── quantum/               # Drop quantum docs here
│   ├── robotics/              # Drop robotics docs here
│   ├── infrastructure/        # GPU/CUDA/NVIDIA docs
│   ├── world_models/          # World model research
│   ├── linear_algebra/        # Math foundations
│   ├── research_papers/       # General research
│   └── google_drive/          # Symlinked Google Drive
├── profiles/
│   ├── mac.yaml               # MacBook (8 GB) profile
│   ├── jetson.yaml            # Edge node profile
│   └── cluster.yaml           # Lab GPU server profile
├── scripts/
│   ├── domain_router.py       # Query → domain classifier
│   ├── ingest_drive.py        # Drive → vector store pipeline
│   ├── nexus_query.py         # Query engine with traces
│   └── benchmark_models.sh   # SLM benchmark lab
├── vector_stores/             # Qdrant persistent storage
├── logs/                      # Benchmark + ingestion logs
└── docker-compose.yaml        # Qdrant + Open WebUI
```

---

## Use Cases

| Use Case | Description |
|---|---|
| **AI Infrastructure Learning** | Students query and see full pipeline traces |
| **Research Knowledge Engine** | Searchable corpus of AARI research |
| **Model Benchmark Lab** | Compare phi3, qwen2.5, gemma2 side-by-side |
| **Edge AI Deployment** | Same system runs on Mac → Jetson → cluster |
| **Robotics + AI Integration** | Domain-routed IK, SLAM, sensor reasoning |
| **Quantum-Classical Interface** | CUDA-Q hook for circuit generation |

---

## Deployment Profiles

| Profile | Hardware | Use |
|---|---|---|
| `mac` | MacBook 8 GB | Development terminal |
| `jetson` | NVIDIA Jetson | Physical lab AI node |
| `cluster` | GPU workstation | Production research |

---

## NVIDIA Pitch

```
AARI-NEXUS = local intelligence platform for AI infrastructure education

User Query
     ↓
Domain Router
     ↓
Vector Store (6 domains)
     ↓
SLM Selection
     ↓
Response + Trace
```

Demonstrates: domain routing · CUDA-Q hook · Jetson deployment · lab cluster profile

---

## Aligns With AARI Thesis

```
Energy → Chips → Infrastructure → Models → Applications
                      ↑               ↑
                   NEXUS sits here (Infrastructure + Models layer)
```

---

## Setup

```bash
# Install Ollama
brew install ollama

# Pull models
ollama pull phi3:mini
ollama pull qwen2.5:3b
ollama pull gemma2:2b
ollama pull nomic-embed-text

# Start vector store + UI
docker-compose up -d

# Connect Google Drive (after installing Google Drive for Desktop)
ln -s ~/Library/CloudStorage/GoogleDrive-*/My\ Drive ~/aari-nexus/data/google_drive
```

---

*AARI — Atlanta AI & Robotics Institute*
