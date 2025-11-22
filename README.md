# Network Transport Optimization Solver

Implementation of the network simplex method for minimum-cost flow problems. Provides both automated batch solving and interactive step-by-step visualization.

## Overview

This library solves capacitated network transport problems where:
- Sources supply goods with positive balance
- Sinks demand goods with negative balance
- Transit nodes conserve flow with zero balance
- Each edge has associated cost and capacity constraints

The solver finds minimum-cost flows satisfying all node balance requirements and edge capacities using the network simplex algorithm with two-phase initialization.

The perfomance wasn't the goal, the goal was to write comprehensive, supportable production code.

## Core Features

**Solver Engine:**
- Network simplex algorithm with basis tree management
- Two-phase initialization for feasible starting solutions
- Automatic handling of capacity constraints
- Configurable optimization strategies via dependency injection

**Interactive Visualization:**
- Real-time algorithm state visualization
- Step-by-step execution with forward/backward navigation
- Interactive graph layout configuration
- Color-coded solution states and basis tree highlighting

## Installation

```bash
pip install matplotlib numpy
```

### Web Interface (Optional)

For web-based visualization:

```bash
python3 task_1_web.py
```

Open browser at `http://localhost:8988` for interactive web interface.

## Quick Start

```python
from network_transport import Graph, run_interactive_demo

# Create network graph
graph = Graph()
graph.add_node("Source1", balance=50)
graph.add_node("Sink1", balance=-50)
graph.add_edge("Source1", "Sink1", cost=10, capacity=100)

# Run interactive solver
run_interactive_demo(graph, "Transport Problem")
```

## Usage Patterns

### Automated Solving

Complete solution without intermediate interaction. The algorithm executes from start to finish automatically.

```python
from network_transport import Graph, TransportSolver

graph = create_my_network()
solver = TransportSolver(graph)
solver.solve_step_by_step()

# Access optimal solution
state = solver.current_state
print(f"Objective value: {state.objective_value}")
print(f"Optimal flows: {state.flows}")
```

### Concurrent Solving of Single Graph

Solve the same graph with different strategy configurations simultaneously for comparison or testing.

```python
from network_transport import Graph, TransportSolver
from network_transport.solver.strategies import PhaseOneInitializer
from network_transport import Graph

import concurrent.futures

graph: Graph = create_my_network()

def solve_with_config(config_name, **strategies):
    solver = TransportSolver(graph, **strategies)
    solver.solve_step_by_step()
    return config_name, solver.current_state

# Define different configurations
configs = [
    ("Default", {}),
    ("Custom Init", {"initialization_strategy": PhaseOneInitializer()}),
]

# Solve concurrently
with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(solve_with_config, name, **kwargs) 
               for name, kwargs in configs]
    
    for future in concurrent.futures.as_completed(futures):
        name, state = future.result()
        print(f"{name}: objective = {state.objective_value}")
```

### Interactive Session

```python
from network_transport import Graph, SolverController
from network_transport.ui import InteractiveSession, LayoutContext

graph = create_my_network()
layout = LayoutContext()
controller = SolverController(graph)

session = InteractiveSession(graph, layout, controller)
session.setup_and_run()
```

### Programmatic Control

```python
from network_transport import SolverController

controller = SolverController(graph)

while controller.can_go_next():
    controller.next_step()
    current = controller.get_current_state()
    print(f"Step {current.iteration}: {current.description}")
```

### Two-Phase Visualization

Interactive demonstration of both phases of the network simplex algorithm:

```python
# Run task_1_two_phase.py to see:
# - Phase 1: Find initial feasible solution using auxiliary problem
# - Phase 2: Optimize the solution for minimum cost

python task_1_two_phase.py
```

This demonstrates:
- Auxiliary graph construction with artificial root node
- Minimization of artificial flow to find initial feasible basis
- Extraction of feasible basis for the original problem
- Optimization to minimum cost starting from feasible basis

### Console Output in Sidebar

Display algorithm output directly in the visualization sidebar:

```python
from network_transport import Graph, run_interactive_demo

graph = create_my_network()

run_interactive_demo(
    graph,
    title="My Transport Problem",
    show_console_in_sidebar=True  # Enable console display in sidebar
)
```

Features:
- All solver steps and calculations displayed in sidebar
- Toggle between console log and problem statistics using "Console" button
- Complete step log with automatic text wrapping (55 char width)
- Each step replaces previous in sidebar (no accumulation)
- Centralized logging: all output (steps, instructions, system messages) handled by `SolutionLogger`
- Useful for understanding algorithm decisions without terminal access

## Examples

Three demonstration problems are included:

**task_1.py** - Railway cargo transportation with 7 stations and 12 routes. Demonstrates basic uncapacitated transport optimization.

**task_2.py** - Capacitated network planning with 8 nodes and 15 edges. Shows handling of upper bound constraints on edge flows.

**task_1_two_phase.py** - Interactive two-phase demonstration showing both Phase 1 (finding feasible solution) and Phase 2 (optimization) separately.

Run examples:
```bash
python task_1.py
python task_2.py
python task_1_two_phase.py
```

## Architecture

The library follows strict separation of concerns:

**Core Layer** (`models/`, `solver/`):
- Pure domain logic with no UI dependencies
- Graph representation and algorithm implementation
- Strategy pattern for extensible optimization components

**UI Layer** (`ui/`):
- Matplotlib-based visualization
- Interactive session management
- Layout configuration and rendering

**Logging Layer** (`logging/`):
- Formatted console output
- Solution state reporting

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design documentation.

## API Reference

Complete API documentation available in [API.md](API.md).

## Requirements

- Python 3.12+
- matplotlib >= 3.10.7
- numpy >= 2.3.5

## Project Structure

```
network_transport/
├── models/          # Domain models (Graph, Node, Edge)
├── solver/          # Algorithm implementation
│   └── strategies/  # Strategy pattern components
├── ui/              # Visualization and interaction
│   └── renderers/   # Rendering components
└── logging/         # Output formatting
```

## License

Academic project for optimization methods coursework.
