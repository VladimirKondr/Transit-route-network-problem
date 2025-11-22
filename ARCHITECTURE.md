# Architecture Documentation

This document describes the architectural design and implementation patterns of the Network Transport Optimization Solver.

## Architecture Diagrams

The project directory contains visual representations of the system architecture:

- **Core Architecture** (`transport_core.png`, `transport_core.svg`, `transport_core.graphml`): Essential modules and their relationships (Core, Solver, Models)
- **Full Architecture** (`transport_full.png`, `transport_full.svg`, `transport_full.graphml`): Complete system including UI, but without logging.

## System Architecture

### Three-Layer Architecture

```
┌─────────────────────────────────────┐
│         UI Layer                    │
│  - Interactive visualization        │
│  - Layout management                │
│  - Event handling                   │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│         Core Layer                  │
│  - Domain models (Graph/Node/Edge)  │
│  - Solver algorithm                 │
│  - Strategy components              │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│      Logging Layer                  │
│  - Formatted console output         │
└─────────────────────────────────────┘
```

**Layer Dependencies:**
- UI Layer depends on Core Layer
- Core Layer has no dependencies on UI
- Logging Layer depends on Core Layer only

This structure enables:
- Headless batch solving without UI
- Unit testing of algorithm logic independently
- Multiple UI implementations (CLI, web, desktop)

## Core Layer Architecture

### Domain Models

Pure data structures with no algorithm or UI dependencies.

**Graph:**
- Container managing network topology
- Provides query methods for navigation
- Validates structural invariants

**Node:**
- Immutable node with balance property
- Type derived automatically from balance sign
- Frozen dataclass for safety

**Edge:**
- Immutable directed edge with cost and capacity
- Frozen dataclass for safety
- Default infinite capacity

### Solver Architecture

```
┌────────────────────────────────────────────────────┐
│           TransportSolverBase (Abstract)           │
│  - Defines solver contract                         │
│  - Strategy injection interface                    │
└───────────────────┬────────────────────────────────┘
                    │
┌───────────────────▼────────────────────────────────┐
│           TransportSolver (Concrete)               │
│  - Network simplex implementation                  │
│  - Orchestrates strategy execution                 │
│  - Maintains state and history                     │
└───────────────────┬────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼──────┐       ┌───────▼──────────┐
│  SolverController    │   Strategy         │
│  - High-level API    │   Implementations  │
│  - Step navigation   │   - Initialization │
│  - State history     │   - Potentials     │
└──────────────────────┘   - Optimality     │
                       │   - Cycle finding  │
                       │   - Theta calc     │
                       │   - Flow update    │
                       └────────────────────┘
```

### Strategy Pattern Implementation

The solver uses six pluggable strategies for algorithm phases:

**1. InitializationStrategy**

Finds initial feasible basis and flows.

**Default Implementation:** `PhaseOneInitializer`
- Constructs auxiliary graph with artificial root
- Adds artificial edges with high cost
- Solves auxiliary problem to minimize artificial flows
- Extracts feasible basis for original problem

**Algorithm Flow:**
1. Validate total balance = 0
2. Create auxiliary graph with artificial root node
3. Add edges: root → sinks (cost=1), sources → root (cost=1)
4. Initialize flows on artificial edges = |balance|
5. Solve auxiliary problem with network simplex
6. If optimal value > 0, problem infeasible
7. Extract original basis, eliminating artificial edges

**2. PotentialCalculationStrategy**

Computes node potentials from basis tree.

**Default Implementation:** `PotentialCalculator`
- BFS traversal of basis spanning tree
- Maintains potential relationship: u_j = u_i + c_ij for basis edges

**Algorithm:** Set root potential to 0, traverse tree updating potentials

**3. OptimalityCheckStrategy**

Tests KKT optimality conditions and selects entering variable.

**Default Implementation:** `OptimalityChecker`
- Computes reduced costs: δ_ij = u_j - u_i - c_ij
- Identifies violations:
  - At lower bound (flow=0): δ > 0 → can increase flow
  - At upper bound (flow=capacity): δ < 0 → can decrease flow
- Selects maximum violation for entering edge

**4. CycleFindingStrategy**

Identifies cycle formed when entering edge added to basis.

**Default Implementation:** `CycleFinder`
- Constructs undirected adjacency from basis tree
- DFS to find tree path connecting entering edge endpoints
- Combines entering edge + tree path = cycle
- Assigns signs (+ / -) to edges for flow adjustment

**5. ThetaCalculationStrategy**

Computes maximum feasible flow change along cycle.

**Default Implementation:** `ThetaCalculator`
- For edges with sign "-": theta ≤ current_flow
- For edges with sign "+": theta ≤ capacity - current_flow
- Theta = minimum bottleneck
- Identifies leaving edge (reaches bound)

**6. FlowUpdateStrategy**

Updates flows and swaps basis edges.

**Default Implementation:** `FlowUpdater`
- Adjusts flows along cycle: flow ± theta
- Removes leaving edge from basis
- Adds entering edge to basis
- Returns updated flows and basis sets

### State Management

**SolutionState (Immutable Snapshot):**
```python
@dataclass(frozen=True)
class SolutionState:
    step_type: StepType           # Algorithm phase
    iteration: int                # Iteration counter
    basis_edges: Set[...]         # Current basis
    non_basis_edges: Set[...]     # Non-basis edges
    potentials: Dict[str, float]  # Node potentials
    deltas: Dict[..., float]      # Reduced costs
    flows: Dict[..., float]       # Edge flows
    entering_edge: Optional[...]  # Selected entering edge
    leaving_edge: Optional[...]   # Selected leaving edge
    improvement_direction: str    # "increase" or "decrease"
    cycle: List[CycleEdge]        # Improvement cycle
    theta: float                  # Flow adjustment
    description: str              # Human-readable description
    objective_value: float        # Total cost
```

**StepType Enumeration:**
```
INITIAL_STATE → INITIAL_BASIS → CALCULATE_POTENTIALS → 
CHECK_OPTIMALITY → FIND_CYCLE → CALCULATE_THETA → 
UPDATE_FLOWS → [repeat from CALCULATE_POTENTIALS] → OPTIMAL
```


## UI Layer Architecture

### Component Hierarchy

```
┌────────────────────────────────────────┐
│       InteractiveSession               │
│  - Session coordinator                 │
│  - Event handling                      │
│  - Mode transitions                    │
└──────────┬─────────────────────────────┘
           │
    ┌──────┴──────┐
    │             │
┌───▼────┐   ┌───▼─────────────┐
│ Logger │   │ GraphVisualizer │
└────────┘   └───┬─────────────┘
                 │
         ┌───────┴────────┐
         │                │
    ┌────▼─────┐   ┌─────▼─────┐
    │ Layout   │   │ Renderers │
    │ Context  │   │ - Nodes   │
    └──────────┘   │ - Edges   │
                   │ - Legend  │
                   │ - Sidebar │
                   └───────────┘
```

## Data Flow

### Batch Solving Flow

```
Graph → TransportSolver.solve_step_by_step() → 
[Strategy Executions] → History[SolutionState] → 
Access final state
```

### Interactive Solving Flow

```
Graph → SolverController → 
User interaction (next/previous) →
Controller.next_step() → Solver.step() →
New SolutionState → 
LayoutContext + State → GraphVisualizer.draw_solution_step() →
Rendered visualization
```

### Layout Configuration Flow

```
Graph + empty LayoutContext → 
InteractiveSession.setup_and_run() →
GraphVisualizer.setup_interactive_layout() →
User positions nodes/labels →
LayoutContext.fix_layout() →
Transition to solver mode (same window) →
Interactive solving begins
```

## Extension Points

### Custom Strategies

Implement strategy interfaces for custom behavior:

```python
class MyInitializer(InitializationStrategy):
    def execute(self, graph: Graph) -> BasisResult:
        # Custom initialization logic
        return BasisResult(basis_edges, non_basis_edges, flows)

solver = TransportSolver(graph, initialization_strategy=MyInitializer())
```

### Custom Visualization

Extend rendering components:

```python
class CustomNodeRenderer(NodeRenderer):
    def render(self, node_vm, ax):
        # Custom node appearance
        pass

visualizer.set_node_renderer(CustomNodeRenderer())
```

## File Organization

```
network_transport/
├── __init__.py              # Public API exports
├── utils.py                 # Utility functions (run_interactive_demo)
├── models/                  # Domain models (Core Layer)
│   ├── __init__.py
│   ├── graph.py            # Graph container
│   ├── node.py             # Node with balance
│   └── edge.py             # Edge with cost/capacity
├── solver/                  # Algorithm implementation (Core Layer)
│   ├── __init__.py
│   ├── solver_base.py      # Abstract base class
│   ├── transport_solver.py # Network simplex implementation
│   ├── controller.py       # High-level API
│   ├── utils.py            # State/result data classes
│   ├── solver_factory.py   # Factory type alias
│   └── strategies/         # Strategy implementations
│       ├── __init__.py
│       ├── base.py         # Strategy interfaces
│       ├── initialization.py        # Phase 1 method
│       ├── potential_calculator.py  # BFS potential computation
│       ├── optimality_checker.py    # KKT condition checking
│       ├── cycle_finder.py          # DFS cycle detection
│       ├── theta_calculator.py      # Bottleneck computation
│       └── flow_updater.py          # Flow adjustment
├── ui/                      # Visualization (UI Layer)
│   ├── __init__.py
│   ├── session.py          # Interactive session coordinator
│   ├── visualizer.py       # Matplotlib facade
│   ├── layout_context.py   # Visual state management
│   ├── view_models.py      # Domain → visual transformations
│   ├── interaction_handler.py  # Mouse event handling
│   ├── rendering_adapters.py   # Base renderer classes
│   ├── geometry.py         # Geometric calculations
│   ├── styles.py           # Visual style configuration
│   └── renderers/          # Specialized rendering
│       ├── __init__.py
│       ├── legend.py       # Legend rendering
│       └── sidebar.py      # Info panel rendering
└── logging/                 # Console output (Logging Layer)
    ├── __init__.py
    └── solution_logger.py  # Formatted state logging
```
