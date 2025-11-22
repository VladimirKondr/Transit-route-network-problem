"""
Network Transport Problem Solver Library

Core Layer (domain logic, no UI dependencies):
    - models: Pure domain models (Graph, Node, Edge)
    - solver: Algorithm logic (TransportSolver, SolverController, strategies)

UI Layer (visualization and interaction):
    - ui: All visualization and user interaction components
    - ui.LayoutContext: Separates visual state from domain models

Logging Layer:
    - logging: Console output formatting

For interactive solving, use:
    from network_transport.ui import InteractiveSession, LayoutContext
"""

# Core domain models
from .models.graph import Graph
from .models.node import Node, NodeType
from .models.edge import Edge

# Core solver (can be used without UI)
from .solver.transport_solver import TransportSolver, SolutionState, StepType
from .solver.controller import SolverController

# Utilities
from .utils import run_interactive_demo

__version__ = "0.2.0"
__all__ = [
    "Graph", "Node", "NodeType", "Edge",
    "TransportSolver", "SolutionState", "StepType",
    "SolverController",
    "run_interactive_demo"
]
