# CUDA-Q Primer — AARI Quantum Workshop

## What is CUDA-Q?

CUDA-Q is NVIDIA's open-source platform for hybrid quantum-classical computing.
It allows developers to write quantum circuits that execute on:
- Simulated QPUs (on GPU or CPU)
- Real quantum hardware (via cloud providers)
- NVIDIA GPU accelerated simulators

CUDA-Q uses a kernel-based programming model — quantum code is written as
`__qpu__` kernels and called from classical C++ or Python.

## Key Concepts

### Qubits
A qubit is the fundamental unit of quantum information.
Unlike a classical bit (0 or 1), a qubit can be in superposition:
  |ψ⟩ = α|0⟩ + β|1⟩
where |α|² + |β|² = 1.

### Quantum Gates
- **H (Hadamard):** Creates superposition from |0⟩ → (|0⟩ + |1⟩)/√2
- **CNOT:** Entangles two qubits — flips target if control is |1⟩
- **Rz(θ):** Rotation around Z-axis by angle θ
- **X gate:** Quantum NOT — flips |0⟩ ↔ |1⟩

### Entanglement
Two qubits are entangled when the state of one instantly determines the other,
regardless of distance. Bell state:
  |Φ+⟩ = (|00⟩ + |11⟩)/√2

## VQE — Variational Quantum Eigensolver

VQE is a hybrid quantum-classical algorithm for finding ground state energies.
Used in chemistry simulation (e.g. lithium battery molecules).

**Pipeline:**
1. Prepare parameterized ansatz circuit
2. Measure expectation value of Hamiltonian
3. Classical optimizer adjusts parameters
4. Repeat until energy converges

**AARI Application:**
Students simulate Li₂ molecule ground state energy using CUDA-Q on NVIDIA GPUs.
The VQE result maps to bond dissociation energy — relevant to battery chemistry.

## CUDA-Q Code Pattern (Python)

```python
import cudaq

@cudaq.kernel
def bell_state():
    q = cudaq.qvector(2)
    h(q[0])
    cx(q[0], q[1])

counts = cudaq.sample(bell_state)
print(counts)  # {'00': ~500, '11': ~500}
```

## AARI Workshop — March 5 Session Notes

**Topic:** Lithium battery VQE simulation
**Hardware:** Azure Quantum + NVIDIA GPU simulation
**Stack:** CUDA-Q → Python orchestration → Raspberry Pi edge inference
**Students:** Observed superposition collapse, ran 3-qubit Bell state
**Next step:** Extend to 4-qubit ansatz for more accurate Li₂ energy

## Relevant NVIDIA Resources

- CUDA-Q GitHub: https://github.com/NVIDIA/cuda-quantum
- NVIDIA Quantum docs: https://nvidia.github.io/cuda-quantum/
- JR1999354 — CUDA-Q Academic TME position (application target)
