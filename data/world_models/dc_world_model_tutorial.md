# World Models — DC Tutorial Notes
## Based on Daniel's Washington DC World Model Session

## What is a World Model?

A world model is an internal representation that an AI agent builds of its environment.
Instead of reacting directly to observations, the agent learns to:
1. Predict future states
2. Imagine trajectories without acting in the real world
3. Plan using the imagined model

**Key insight:** Intelligence = compressed, predictive representation of reality.

## Core Architecture — Dreamer / RSSM

The Recurrent State Space Model (RSSM) is the foundation of DreamerV3.

**Components:**

| Module | Role |
|---|---|
| Encoder | Compresses observation → latent state |
| RSSM | Predicts next latent state (with and without observations) |
| Decoder | Reconstructs observation from latent state |
| Reward model | Predicts reward from latent state |
| Actor-Critic | Plans in latent space |

**State representation:**
- Stochastic state: captures uncertainty
- Deterministic state: captures history via GRU

## Latent Space

The latent space is a compressed, continuous representation of the world.
Key properties:
- Lower dimensional than raw observations
- Smooth — nearby points = similar states
- Predictable — transition model operates in this space

## Training Loop

```
Observe environment → encode → latent state
                                    ↓
                            predict next state (RSSM)
                                    ↓
                            imagine K-step rollout
                                    ↓
                            train actor-critic on imagination
                                    ↓
                            act → collect real data → repeat
```

## Why World Models Matter for AARI

1. **Robotics:** Robot learns to plan arm movements by imagining trajectories
2. **Edge AI:** Model runs on Jetson — no cloud needed for planning
3. **Sample efficiency:** Agent learns from imagination, not just real experience
4. **NVIDIA relevance:** DreamerV3 runs best on GPU — ties directly to CUDA stack

## Connection to AARI Infrastructure Thesis

```
Energy → Chips → Infrastructure → Models → Applications
                                     ↑
                              World Models sit here
                         (learned compressed representations)
```

Training world models requires:
- GPU compute (NVIDIA H100/A100)
- Large replay buffers (NVMe storage)
- Fast inference (Jetson at edge)

## Research Pointers

- DreamerV3 (Hafner et al., 2023) — General algorithm across domains
- TDMPC2 — World model for continuous control
- JEPA (LeCun) — Joint Embedding Predictive Architecture
- Genie (Google DeepMind) — Generative world model from video

## AARI Lab Next Steps

- Implement DreamerV3 on simple robotic task (CartPole → arm)
- Profile GPU memory usage on NVIDIA cluster
- Deploy lightweight world model inference on Jetson
- Connect to NEXUS: students query world model docs, get grounded answers
