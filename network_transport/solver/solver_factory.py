from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from network_transport.solver.solver_base import TransportSolverBase

from network_transport.models.graph import Graph


class SolverFactory(Protocol):
    def __call__(self, graph: Graph, **strategies: Any) -> "TransportSolverBase":
        ...