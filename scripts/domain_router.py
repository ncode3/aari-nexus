#!/usr/bin/env python3
"""
AARI-NEXUS Domain Router
Routes queries to the correct domain vector store using few-shot classification.
"""

import re
from dataclasses import dataclass
from typing import Optional

# ── Domain definitions ───────────────────────────────────────────────────────

DOMAINS = [
    "quantum",
    "robotics",
    "infrastructure",
    "world_models",
    "linear_algebra",
    "research_papers",
]

# Few-shot keyword map — extend freely
DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "quantum": [
        "qubit", "superposition", "entanglement", "quantum circuit",
        "variational", "vqe", "cuda-q", "quantum gate", "bloch sphere",
        "hadamard", "decoherence", "quantum error", "lithium battery simulation",
        "quantum algorithm", "qiskit", "pennylane",
    ],
    "robotics": [
        "robot", "kinematics", "inverse kinematics", "actuator", "sensor",
        "ros", "servo", "trajectory", "end effector", "manipulation",
        "slam", "lidar", "odometry", "pid controller", "torque", "joint",
        "forward kinematics", "jacobian", "arm", "degrees of freedom",
    ],
    "infrastructure": [
        "cuda", "gpu", "nvidia", "memory hierarchy", "bandwidth", "tensor core",
        "cuda core", "nvlink", "pcie", "inference", "throughput", "latency",
        "vram", "hbm", "compute", "kernel", "parallel", "driver", "jetson",
        "docker", "container", "cluster", "node",
    ],
    "world_models": [
        "world model", "latent space", "dreamer", "rssm", "prediction",
        "imagination", "model-based", "environment model", "state space",
        "temporal", "transition model", "representation learning",
    ],
    "linear_algebra": [
        "matrix", "matrices", "vector", "eigenvalue", "eigenvalues",
        "eigenvector", "eigenvectors", "determinant", "transpose",
        "dot product", "cross product", "norm", "span", "basis",
        "orthogonal", "svd", "singular value", "rank",
        "linear transformation", "projection", "null space",
        "linear algebra", "pca", "least squares",
    ],
    "research_papers": [
        "paper", "arxiv", "study", "research", "survey", "literature",
        "findings", "methodology", "abstract", "conclusion", "citation",
        "published", "journal", "conference", "nips", "icml", "iclr",
    ],
}


@dataclass
class RouteResult:
    domain: str
    confidence: str        # "high" | "medium" | "low"
    matched_keywords: list[str]
    fallback: bool = False


def route_query(query: str) -> RouteResult:
    """
    Route a query to the best-matching domain.
    Uses keyword scoring with few-shot examples.
    Returns RouteResult with domain, confidence, and matched terms.
    """
    q = query.lower()
    scores: dict[str, int] = {d: 0 for d in DOMAINS}
    matched: dict[str, list[str]] = {d: [] for d in DOMAINS}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", q):
                scores[domain] += 1
                matched[domain].append(kw)

    best_domain = max(scores, key=lambda d: scores[d])
    best_score = scores[best_domain]

    if best_score == 0:
        return RouteResult(
            domain="research_papers",
            confidence="low",
            matched_keywords=[],
            fallback=True,
        )

    confidence = "high" if best_score >= 3 else "medium" if best_score >= 1 else "low"

    return RouteResult(
        domain=best_domain,
        confidence=confidence,
        matched_keywords=matched[best_domain],
    )


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_queries = [
        "What is a qubit and how does superposition work?",
        "Explain inverse kinematics for a 3-joint robot arm",
        "How does CUDA memory hierarchy affect inference throughput?",
        "What is the Dreamer world model architecture?",
        "Explain eigenvalues and eigenvectors",
        "Summarize Jensen Huang's GPU architecture strategy",
        "How do I compute the Jacobian for a manipulator?",
    ]

    print("\n── AARI-NEXUS Domain Router Test ──\n")
    for q in test_queries:
        result = route_query(q)
        flag = " [FALLBACK]" if result.fallback else ""
        print(f"Query : {q[:60]}")
        print(f"Domain: {result.domain} | Confidence: {result.confidence}{flag}")
        print(f"Matched: {result.matched_keywords}")
        print()
