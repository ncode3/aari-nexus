# AARI — NVIDIA Partnership Brief

## Atlanta AI & Robotics Institute (AARI)

AARI is an AI and robotics education initiative focused on building the next
generation of AI infrastructure engineers, roboticists, and quantum computing
practitioners.

**Core thesis:**
> The talent pipeline for AI infrastructure is broken.
> Most AI education stops at prompting APIs.
> AARI teaches the full stack: chips → infrastructure → models → applications.

## AARI-NEXUS Platform

AARI-NEXUS is the operational intelligence layer of the AARI lab.

**Architecture:**
```
User Query
     ↓
Domain Router  (6 domains: quantum, robotics, infrastructure,
                            world_models, linear_algebra, research_papers)
     ↓
Domain Vector Store  (Qdrant, fully local)
     ↓
SLM Selection  (phi3:mini | qwen2.5:3b | gemma2:2b)
     ↓
Response + Observability Trace
```

**What makes it different from ChatGPT:**
Students see the full trace — domain routing decision, model selected,
documents retrieved, embedding latency, generation latency.
They learn the mechanics of AI, not just the output.

## Hardware Stack

| Layer | Hardware | Role |
|---|---|---|
| Development | MacBook Air 8 GB | Control terminal |
| Edge | NVIDIA Jetson Orin NX | Physical student AI node |
| Cluster | GPU workstation (NVIDIA RTX/A100) | Research + production |

## CUDA-Q Integration

NEXUS includes a CUDA-Q hook for quantum workflow:

```
Student asks natural language question about quantum circuit
     ↓
NEXUS routes to Quantum domain
     ↓
phi3:mini explains circuit theory from AARI research docs
     ↓
CUDA-Q executes simulation on NVIDIA GPU
     ↓
Results returned with explanation
```

**Current experiments:**
- Lithium battery VQE simulation (Azure Quantum + GPU sim)
- 3-qubit Bell state → 4-qubit Li₂ ansatz
- Student observes superposition collapse in real time

## Workshop: Three-Tier AI Pipeline

AARI's March 26 workshop demonstrates:

**Tier 1 — Cloud quantum (Azure Quantum):**
VQE simulation of molecular ground state energy

**Tier 2 — Python orchestration:**
Classical optimizer controls quantum parameter updates

**Tier 3 — Edge inference (Raspberry Pi / Jetson):**
Lightweight model explains results at the edge

NEXUS sits above all three tiers as the intelligence and knowledge layer.

## NVIDIA Alignment

| AARI Capability | NVIDIA Product |
|---|---|
| CUDA-Q quantum simulation | CUDA-Q platform |
| GPU cluster inference | DGX / RTX workstation |
| Jetson edge deployment | Jetson Orin NX |
| Local SLM reasoning | NIM microservices pattern |
| Benchmark lab | NVIDIA MLPerf methodology |

## Target Partnership

**Position:** JR1999354 — CUDA-Q Academic Technical Marketing Engineer

**Ask:** NVIDIA academic hardware access for:
- Jetson Orin NX (edge AI node for student lab)
- GPU workstation (cluster profile deployment)
- CUDA-Q developer partnership

**What AARI offers NVIDIA:**
- Student pipeline trained on NVIDIA stack from day one
- Real curriculum built on CUDA-Q (not simulated)
- Demonstrable local AI infrastructure — not a pitch deck

## One-Line Description (for Monica)

> AARI-NEXUS is a local AI knowledge and experimentation platform that teaches
> students how modern AI systems actually work — from chips to inference.
