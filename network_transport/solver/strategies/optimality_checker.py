from typing import Dict, List, Set, Optional, Tuple

from ...models.graph import Graph
from .base import OptimalityCheckStrategy, OptimalityResult
from ...models.edge import EPSILON


class OptimalityChecker(OptimalityCheckStrategy):
    def execute(
        self,
        graph: Graph,
        non_basis_edges: Set[Tuple[str, str]],
        potentials: Dict[str, float],
        flows: Dict[Tuple[str, str], float]
    ) -> OptimalityResult:
        deltas = self._calculate_all_deltas(graph, non_basis_edges, potentials)
        violations = self._collect_violations(graph, non_basis_edges, deltas, flows)
        
        if len(violations) == 0:
            return self._create_optimal_result(deltas)
        
        return self._create_non_optimal_result(deltas, violations)
    
    def _calculate_all_deltas(
        self,
        graph: Graph,
        non_basis_edges: Set[Tuple[str, str]],
        potentials: Dict[str, float]
    ) -> Dict[Tuple[str, str], float]:
        """
        Calculate reduced costs for all non-basis edges.
        """
        deltas: Dict[Tuple[str, str], float] = {}
        
        for edge_id in sorted(non_basis_edges):
            edge = graph.get_edge(*edge_id)
            assert edge is not None

            u_i = potentials[edge.from_node]
            u_j = potentials[edge.to_node]
            
            delta = u_j - u_i - edge.cost
            deltas[edge_id] = delta
        
        return deltas
    
    def _collect_violations(
        self,
        graph: Graph,
        non_basis_edges: Set[Tuple[str, str]],
        deltas: Dict[Tuple[str, str], float],
        flows: Dict[Tuple[str, str], float]
    ) -> List[Tuple[float, Tuple[str, str], str]]:
        """
        Identify edges violating optimality conditions and improvement directions.
        """
        violations: List[Tuple[float, Tuple[str, str], str]] = []
        
        for edge_id in sorted(non_basis_edges):
            violation = self._check_single_violation(graph, edge_id, deltas, flows)
            if violation is not None:
                violations.append(violation)
        
        return violations
    
    def _check_single_violation(
        self,
        graph: Graph,
        edge_id: Tuple[str, str],
        deltas: Dict[Tuple[str, str], float],
        flows: Dict[Tuple[str, str], float]
    ) -> Optional[Tuple[float, Tuple[str, str], str]]:
        edge = graph.get_edge(*edge_id)
        assert edge is not None

        delta = deltas.get(edge_id)
        if delta is None:
            return None
        
        flow = flows.get(edge_id, 0.0)
        is_empty = flow <= EPSILON
        is_saturated = flow >= edge.capacity - EPSILON
        
        if is_empty and delta > EPSILON:
            return (delta, edge_id, "increase")
        elif is_saturated and delta < -EPSILON:
            return (abs(delta), edge_id, "decrease")
        
        return None
    
    def _create_optimal_result(
        self,
        deltas: Dict[Tuple[str, str], float]
    ) -> OptimalityResult:
        return OptimalityResult(
            is_optimal=True,
            deltas=deltas,
            entering_edge=None,
            improvement_direction=None
        )
    
    def _create_non_optimal_result(
        self,
        deltas: Dict[Tuple[str, str], float],
        violations: List[Tuple[float, Tuple[str, str], str]]
    ) -> OptimalityResult:
        entering_edge, direction, score = self._select_best_violation(violations)
        
        return OptimalityResult(
            is_optimal=False,
            deltas=deltas,
            entering_edge=entering_edge,
            improvement_direction=direction,
            violation_score=score
        )
    
    def _select_best_violation(
        self,
        violations: List[Tuple[float, Tuple[str, str], str]]
    ) -> Tuple[Tuple[str, str], str, float]:
        """
        Select entering variable using steepest-edge rule.
        """
        violations.sort(key=lambda x: (-x[0], x[1][0], x[1][1]))
        score, edge_id, direction = violations[0]
        return edge_id, direction, score
