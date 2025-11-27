
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from dataclasses import dataclass
from typing import Dict, Optional, Set, Tuple

from network_transport.models.edge import Edge


# Initialization Strategy

@dataclass
class BasisResult:
    """Result of initialization strategy."""
    basis_edges: Set[Tuple[str, str]]
    non_basis_edges: Set[Tuple[str, str]]
    flows: Dict[Tuple[str, str], float]


# Optimality Checking Strategy

@dataclass
class OptimalityResult:
    """Result of optimality check."""
    is_optimal: bool
    deltas: Dict[Tuple[str, str], float]
    entering_edge: Optional[Tuple[str, str]]
    improvement_direction: Optional[str]
    violation_score: float = 0.0


# Cycle Finding Strategy

@dataclass(slots=True)
class CycleEdge:
    """Edge in cycle with sign and flow limit."""
    edge: Edge
    sign: str  # "+" or "-"
    theta_limit: float


class StepType(Enum):
    INITIAL_STATE = "initial_state"
    INITIAL_BASIS = "initial_basis"
    CALCULATE_POTENTIALS = "calculate_potentials"
    CHECK_OPTIMALITY = "check_optimality"
    FIND_CYCLE = "find_cycle"
    CALCULATE_THETA = "calculate_theta"
    UPDATE_FLOWS = "update_flows"
    OPTIMAL = "optimal"


@dataclass(slots=True, frozen=True)
class SolutionState:
    """Solver state snapshot."""
    step_type: StepType = StepType.INITIAL_STATE
    iteration: int = -1
    basis_edges: Optional[Set[Tuple[str, str]]] = None
    non_basis_edges: Optional[Set[Tuple[str, str]]] = None
    potentials: Optional[Dict[str, float]] = None
    deltas: Optional[Dict[Tuple[str, str], float]] = None
    flows: Optional[Dict[Tuple[str, str], float]] = None
    entering_edge: Optional[Tuple[str, str]] = None
    leaving_edge: Optional[Tuple[str, str]] = None
    improvement_direction: Optional[str] = None
    cycle: Optional[List[CycleEdge]] = None
    theta: Optional[float] = None
    description: str = ""
    objective_value: float = 0.0

@dataclass(slots=True, frozen=True)
class VamState:
    flows: Dict[Tuple[str, str], float]
    partial_basis: Set[Tuple[str, str]]
    active_supply: Set[str]
    active_demand: Set[str]
    current_supply: Dict[str, float]
    current_demand: Dict[str, float]