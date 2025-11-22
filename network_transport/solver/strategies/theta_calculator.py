from typing import List, Tuple, Optional, Set

from ...models.edge import EPSILON
from .base import ThetaCalculationStrategy, CycleEdge


class ThetaCalculator(ThetaCalculationStrategy):
    def execute(
        self, 
        cycle: List[CycleEdge],
        basis_edges: Optional[Set[Tuple[str, str]]] = None
    ) -> Tuple[float, Optional[Tuple[str, str]]]:

        if not cycle:
            return 0.0, None
        
        self._basis_edges = basis_edges or set()
        theta = self._find_minimum_theta(cycle)
        leaving_edge = self._select_leaving_edge(cycle, theta)
        self._basis_edges: Set[Tuple[str, str]] = set()
        
        return theta, leaving_edge
    
    def _find_minimum_theta(self, cycle: List[CycleEdge]) -> float:
        theta = min(ce.theta_limit for ce in cycle)
        
        if theta == float('inf'):
            theta = 0.0
        
        return theta
    
    def _select_leaving_edge(
        self,
        cycle: List[CycleEdge],
        theta: float
    ) -> Optional[Tuple[str, str]]:
        """Select leaving edge using Bland's rule.
        
        Among edges with theta_limit = theta:
        1. Prefer basis edges (prevents degeneracy)
        2. Break ties lexicographically by (from_node, to_node)
        
        Args:
            cycle: List of cycle edges
            theta: Minimum theta value
            
        Returns:
            Edge ID of leaving edge, or None if no edge limits theta
        """
        candidates = self._find_limiting_edges(cycle, theta)
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda ce: (
            ce.edge.edge_id not in self._basis_edges,
            ce.edge.from_node,
            ce.edge.to_node
        ))
        
        return candidates[0].edge.edge_id
    
    def _find_limiting_edges(
        self,
        cycle: List[CycleEdge],
        theta: float
    ) -> List[CycleEdge]:
        """Find all edges whose limit equals theta."""
        return [
            ce for ce in cycle
            if abs(ce.theta_limit - theta) < EPSILON
        ]
