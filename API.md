# API Reference

Complete reference for the Network Transport Optimization Solver library.

## Core Models

### Graph

Container managing network topology and properties.

```python
class Graph:
    def __init__(self) -> None
    
    def add_node(self, node_id: str, balance: float = 0.0) -> Node
    def add_edge(self, from_node: str, to_node: str, cost: float, 
                 capacity: float = float('inf')) -> Edge
    
    def get_node(self, node_id: str) -> Optional[Node]
    def get_edge(self, from_node: str, to_node: str) -> Optional[Edge]
    
    def get_nodes_by_type(self, node_type: NodeType) -> List[Node]
    def get_outgoing_edges(self, node_id: str) -> List[Edge]
    def get_incoming_edges(self, node_id: str) -> List[Edge]
    def get_adjacent_edges(self, node_id: str) -> List[Edge]
    
    def check_balance_feasibility(self) -> bool
```

**Properties:**
- `nodes: Dict[str, Node]` - All nodes indexed by ID
- `edges: Dict[Tuple[str, str], Edge]` - All edges indexed by (from, to)

### Node

Network node with supply or demand balance.

```python
@dataclass(frozen=True)
class Node:
    id: str
    balance: float = 0.0
    
    @property
    def node_type(self) -> NodeType  # SOURCE, SINK, or TRANSIT
```

**Balance semantics:**
- Positive: Supply node (source)
- Negative: Demand node (sink)
- Zero: Transit node (intermediate)

### Edge

Directed edge with cost and capacity constraints.

```python
@dataclass(frozen=True)
class Edge:
    from_node: str
    to_node: str
    cost: float
    capacity: float = float('inf')
    
    @property
    def edge_id(self) -> Tuple[str, str]
```

### NodeType

```python
class NodeType(Enum):
    SOURCE = "source"
    SINK = "sink"
    TRANSIT = "transit"
```

## Solver Components

### TransportSolver

Main solver implementing the network simplex algorithm.

```python
class TransportSolver(TransportSolverBase):
    MAX_ITERATIONS = 1000
    
    def __init__(
        self,
        graph: Graph,
        initialization_strategy: Optional[InitializationStrategy] = None,
        potential_calculator: Optional[PotentialCalculationStrategy] = None,
        optimality_checker: Optional[OptimalityCheckStrategy] = None,
        cycle_finder: Optional[CycleFindingStrategy] = None,
        theta_calculator: Optional[ThetaCalculationStrategy] = None,
        flow_updater: Optional[FlowUpdateStrategy] = None
    ) -> None
    
    def solve_step_by_step(self) -> None
    def step(self) -> None
    
    @property
    def current_state(self) -> SolutionState
    @property
    def history(self) -> List[SolutionState]
    @property
    def iteration(self) -> int
```

**Strategy Parameters:**

All strategy parameters are optional. Default implementations are provided:

- `initialization_strategy`: Finds initial feasible basis (default: `PhaseOneInitializer`)
- `potential_calculator`: Computes node potentials (default: `PotentialCalculator`)
- `optimality_checker`: Tests KKT conditions (default: `OptimalityChecker`)
- `cycle_finder`: Identifies improvement cycles (default: `CycleFinder`)
- `theta_calculator`: Computes maximum flow adjustment (default: `ThetaCalculator`)
- `flow_updater`: Updates flows and basis (default: `FlowUpdater`)

**Methods:**

- `solve_step_by_step()`: Execute complete solution algorithm
- `step()`: Advance one logical step in algorithm
- `current_state`: Current solution state
- `history`: Complete execution history
- `iteration`: Current iteration number

**Raises:**
- `RuntimeError`: If maximum iterations exceeded
- `ValueError`: If problem infeasible or invalid input

### SolverController

High-level controller for interactive step-by-step solving.

```python
class SolverController:
    def __init__(self, graph: Graph, solver: Optional[TransportSolverBase] = None)
    
    def next_step(self) -> bool
    def previous_step(self) -> bool
    def solve_all(self) -> None
    def reset(self) -> None
    
    def can_go_next(self) -> bool
    def can_go_previous(self) -> bool
    def is_started(self) -> bool
    def is_solved(self) -> bool
    
    def get_current_state(self) -> SolutionState
    def get_all_states(self) -> List[SolutionState]
```

**Navigation Methods:**

- `next_step()`: Advance to next algorithm step. Returns `True` if step executed.
- `previous_step()`: Return to previous state. Returns `True` if successful.
- `solve_all()`: Execute all remaining steps to completion.
- `reset()`: Reset solver to initial state.

**Query Methods:**

- `can_go_next()`: Check if forward navigation possible
- `can_go_previous()`: Check if backward navigation possible
- `is_started()`: Check if solving has begun
- `is_solved()`: Check if optimal solution reached

**State Access:**

- `get_current_state()`: Get current algorithm state
- `get_all_states()`: Get full state history

### SolutionState

Immutable snapshot of algorithm state at specific step.

```python
@dataclass(frozen=True)
class SolutionState:
    step_type: StepType
    iteration: int
    basis_edges: Optional[Set[Tuple[str, str]]]
    non_basis_edges: Optional[Set[Tuple[str, str]]]
    potentials: Optional[Dict[str, float]]
    deltas: Optional[Dict[Tuple[str, str], float]]
    flows: Optional[Dict[Tuple[str, str], float]]
    entering_edge: Optional[Tuple[str, str]]
    leaving_edge: Optional[Tuple[str, str]]
    improvement_direction: Optional[str]  # "increase" or "decrease"
    cycle: Optional[List[CycleEdge]]
    theta: Optional[float]
    description: str
    objective_value: float
```

### StepType

Algorithm execution phases.

```python
class StepType(Enum):
    INITIAL_STATE = "initial_state"
    INITIAL_BASIS = "initial_basis"
    CALCULATE_POTENTIALS = "calculate_potentials"
    CHECK_OPTIMALITY = "check_optimality"
    FIND_CYCLE = "find_cycle"
    CALCULATE_THETA = "calculate_theta"
    UPDATE_FLOWS = "update_flows"
    OPTIMAL = "optimal"
```

## Strategy Interfaces

### InitializationStrategy

```python
class InitializationStrategy(ABC):
    @abstractmethod
    def execute(self, graph: Graph) -> BasisResult
```

**Implementations:**
- `PhaseOneInitializer`: Two-phase method with artificial variables
- `PrebuiltInitializer`: Use pre-computed basis (internal use)

### PotentialCalculationStrategy

```python
class PotentialCalculationStrategy(ABC):
    @abstractmethod
    def execute(self, graph: Graph, basis_edges: Set[Tuple[str, str]]) -> Dict[str, float]
```

**Implementation:** `PotentialCalculator` - BFS tree traversal

### OptimalityCheckStrategy

```python
class OptimalityCheckStrategy(ABC):
    @abstractmethod
    def execute(
        self, graph: Graph, non_basis_edges: Set[Tuple[str, str]],
        potentials: Dict[str, float], flows: Dict[Tuple[str, str], float]
    ) -> OptimalityResult
```

**Implementation:** `OptimalityChecker` - Reduced cost computation and KKT violation detection

### CycleFindingStrategy

```python
class CycleFindingStrategy(ABC):
    @abstractmethod
    def execute(
        self, graph: Graph, basis_edges: Set[Tuple[str, str]],
        entering_edge: Tuple[str, str], direction: str,
        flows: Dict[Tuple[str, str], float]
    ) -> List[CycleEdge]
```

**Implementation:** `CycleFinder` - DFS path finding in basis tree

### ThetaCalculationStrategy

```python
class ThetaCalculationStrategy(ABC):
    @abstractmethod
    def execute(self, cycle: List[CycleEdge]) -> Tuple[float, Optional[Tuple[str, str]]]
```

**Implementation:** `ThetaCalculator` - Minimum bottleneck computation

### FlowUpdateStrategy

```python
class FlowUpdateStrategy(ABC):
    @abstractmethod
    def execute(
        self, flows: Dict[Tuple[str, str], float], cycle: List[CycleEdge],
        theta: float, leaving_edge: Optional[Tuple[str, str]]
    ) -> Tuple[Dict[Tuple[str, str], float], Set[Tuple[str, str]], Set[Tuple[str, str]]]
```

**Implementation:** `FlowUpdater` - Cycle flow adjustment and basis update


## Result Data Classes

### BasisResult

```python
@dataclass
class BasisResult:
    basis_edges: Set[Tuple[str, str]]
    non_basis_edges: Set[Tuple[str, str]]
    flows: Dict[Tuple[str, str], float]
```

### OptimalityResult

```python
@dataclass
class OptimalityResult:
    is_optimal: bool
    deltas: Dict[Tuple[str, str], float]
    entering_edge: Optional[Tuple[str, str]]
    improvement_direction: Optional[str]
    violation_score: float
```

### CycleEdge

```python
@dataclass
class CycleEdge:
    edge: Edge
    sign: str  # "+" or "-"
    theta_limit: float
```

## Constants

```python
EPSILON = 1e-9  # Numerical tolerance for floating-point comparisons
```

## UI Components

### InteractiveSession

Coordinates interactive visualization and solving.

```python
class InteractiveSession:
    def __init__(
        self, graph: Graph, layout: Optional[LayoutContext] = None,
        controller: Optional[SolverController] = None
    )
    
    def setup_and_run(self) -> None
```

**Workflow:**
1. Configure graph layout interactively (if not pre-configured)
2. Initialize solver and visualization
3. Provide step-by-step navigation interface

### LayoutContext

Manages visual state and positioning separately from domain logic.

```python
class LayoutContext:
    def set_node_position(self, node_id: str, x: float, y: float) -> None
    def get_node_position(self, node_id: str) -> Optional[Tuple[float, float]]
    
    def set_edge_label_position(self, edge_id: Tuple[str, str], x: float, y: float) -> None
    def get_edge_label_position(self, edge_id: Tuple[str, str]) -> Optional[Tuple[float, float]]
    
    def fix_layout(self) -> None
    def is_layout_fixed(self) -> bool
    
    def save_to_file(self, filepath: str) -> None
    def load_from_file(self, filepath: str) -> None
```

### GraphVisualizer

Low-level matplotlib visualization facade.

```python
class GraphVisualizer:
    def __init__(self, graph: Graph, layout_context: LayoutContext,
                 style: Optional[VisualStyle] = None)
    
    def setup_interactive_layout(self, done_callback=None) -> None
    def draw_solution_step(self, state: SolutionState) -> None
    def start_interaction(self) -> None
    def close(self) -> None
```

## Utility Functions

### run_interactive_demo

Convenience function eliminating boilerplate for common use case.

```python
def run_interactive_demo(
    graph: Graph,
    title: str,
    info_printer: Optional[Callable[[Graph], None]] = None
) -> None
```

**Parameters:**
- `graph`: Configured network graph
- `title`: Display title for console output
- `info_printer`: Optional callback for printing custom graph information

**Usage:**

```python
from network_transport import Graph, run_interactive_demo

graph = create_my_network()
run_interactive_demo(graph, "My Problem", print_network_info)
```

## Error Handling

**ValueError:**
- Invalid graph configuration (duplicate nodes/edges)
- Problem infeasibility (balance not zero, no feasible solution)
- Invalid edge references

**RuntimeError:**
- Maximum iterations exceeded without convergence
- Algorithm invariant violations

## Thread Safety

The library is not thread-safe. Each solver instance should be used from a single thread.

## Performance Considerations

- Graph construction: O(n + m) where n=nodes, m=edges
- Initialization (Phase 1): O(n³) worst case
- Per iteration: O(n²) average case
- Overall complexity: O(n³) for sparse networks
