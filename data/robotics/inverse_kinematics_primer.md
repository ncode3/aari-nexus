# Inverse Kinematics — AARI Robotics Curriculum

## Forward vs Inverse Kinematics

**Forward Kinematics (FK):**
Given joint angles θ₁, θ₂, ..., θₙ → find end-effector position (x, y, z)

**Inverse Kinematics (IK):**
Given desired end-effector position (x, y, z) → find joint angles θ₁, θ₂, ..., θₙ

IK is the harder problem. Multiple solutions may exist (or none).

## Denavit-Hartenberg (DH) Parameters

Standard convention for describing robot joint geometry.

Each joint i is described by 4 parameters:
| Parameter | Symbol | Description |
|---|---|---|
| Link length | aᵢ | Distance along xᵢ from zᵢ to zᵢ₊₁ |
| Link twist | αᵢ | Angle from zᵢ to zᵢ₊₁ around xᵢ |
| Link offset | dᵢ | Distance along zᵢ from xᵢ₋₁ to xᵢ |
| Joint angle | θᵢ | Angle from xᵢ₋₁ to xᵢ around zᵢ |

## 3-Joint Planar Robot Arm Example

For a 3-DOF planar arm with link lengths L₁, L₂, L₃:

**Forward kinematics:**
```
x = L₁cos(θ₁) + L₂cos(θ₁+θ₂) + L₃cos(θ₁+θ₂+θ₃)
y = L₁sin(θ₁) + L₂sin(θ₁+θ₂) + L₃sin(θ₁+θ₂+θ₃)
φ = θ₁ + θ₂ + θ₃  (end-effector orientation)
```

**Inverse kinematics (geometric solution):**
```python
import numpy as np

def ik_3dof_planar(x, y, phi, L1, L2, L3):
    # Wrist position
    xw = x - L3 * np.cos(phi)
    yw = y - L3 * np.sin(phi)

    # Law of cosines for θ₂
    r = np.sqrt(xw**2 + yw**2)
    cos_theta2 = (r**2 - L1**2 - L2**2) / (2 * L1 * L2)
    theta2 = np.arccos(np.clip(cos_theta2, -1, 1))  # elbow up

    # θ₁
    alpha = np.arctan2(yw, xw)
    beta = np.arctan2(L2 * np.sin(theta2), L1 + L2 * np.cos(theta2))
    theta1 = alpha - beta

    # θ₃
    theta3 = phi - theta1 - theta2

    return theta1, theta2, theta3
```

## The Jacobian

The Jacobian matrix J relates joint velocities to end-effector velocity:

```
ẋ = J(θ) · θ̇
```

For IK velocity control:
```
θ̇ = J⁺ · ẋ
```
where J⁺ is the pseudoinverse of J (Moore-Penrose).

**Singularities:** When J loses rank (det(J) ≈ 0), the arm is at a singularity.
The robot loses a degree of freedom — motion in some direction becomes impossible.

## Numerical IK Methods

When analytical solutions don't exist (redundant robots, 6+ DOF):

**Damped Least Squares (DLS):**
```
θ̇ = Jᵀ(JJᵀ + λ²I)⁻¹ · ẋ
```
λ is a damping factor that prevents instability near singularities.

**FABRIK (Forward And Backward Reaching IK):**
Iterative, position-based. Fast and stable for real-time use.

## AARI Robotics Lab Application

Students build:
1. 3-joint simulated arm in Python/NumPy
2. Compute FK and IK for target positions
3. Visualize with matplotlib
4. (Advanced) Port to ROS2 + real servo arm

**Connection to NEXUS:**
Students ask: "How do I compute IK for a 3-joint arm?"
NEXUS routes to Robotics domain → retrieves this document → phi3:mini explains.
