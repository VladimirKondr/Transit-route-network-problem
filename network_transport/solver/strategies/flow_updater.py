from copy import deepcopy
from typing import List, Set, Tuple, Dict, Optional

from ...models.graph import Graph
from ...models.edge import EPSILON
from .base import FlowUpdateStrategy, CycleEdge


class FlowUpdater(FlowUpdateStrategy):
    def execute(
        self,
        graph: Graph,
        cycle: List[CycleEdge],
        theta: float,
        entering_edge: Tuple[str, str],
        leaving_edge: Optional[Tuple[str, str]],
        current_basis: Set[Tuple[str, str]],
        current_flows: Dict[Tuple[str, str], float]
    ) -> Tuple[Set[Tuple[str, str]], Set[Tuple[str, str]], Dict[Tuple[str, str], float]]:
        new_flows = self._adjust_flows(cycle, theta, current_flows)
        new_basis, new_non_basis = self._update_basis(
            graph, entering_edge, leaving_edge, current_basis
        )
        
        return new_basis, new_non_basis, new_flows
    
    def _adjust_flows(
        self, 
        cycle: List[CycleEdge], 
        theta: float,
        current_flows: Dict[Tuple[str, str], float]
    ) -> Dict[Tuple[str, str], float]:
        """
        Adjust flows along cycle edges.
        
        Flow adjustment:
        - Sign "+": flow += theta
        - Sign "-": flow -= theta
        
        Rounding:
        - |flow| < ε → flow = 0
        - |flow - capacity| < ε → flow = capacity
        """
        new_flows = deepcopy(current_flows)
        
        for cycle_edge in cycle:
            edge_id = cycle_edge.edge.edge_id
            current_flow = new_flows.get(edge_id, 0.0)
            
            if cycle_edge.sign == "+":
                new_flow = current_flow + theta
            else:
                new_flow = current_flow - theta
            
            # Round for numerical stability
            new_flow = self._round_flow_value(new_flow, cycle_edge.edge.capacity)
            new_flows[edge_id] = new_flow
        
        return new_flows
    
    def _round_flow_value(self, flow: float, capacity: float) -> float:
        if abs(flow) < EPSILON:
            return 0.0
        elif abs(flow - capacity) < EPSILON:
            return capacity
        return flow
    
    def _update_basis(
        self,
        graph: Graph,
        entering_edge: Tuple[str, str],
        leaving_edge: Optional[Tuple[str, str]],
        current_basis: Set[Tuple[str, str]]
    ) -> Tuple[Set[Tuple[str, str]], Set[Tuple[str, str]]]:
        """
        Perform basis swap: remove leaving edge, add entering edge.
        
        Degeneracy case: entering_edge = leaving_edge
        In this case, entering edge hits its limit immediately,
        so basis structure remains unchanged.
        
        Returns:
            Tuple of (new_basis_edges, new_non_basis_edges)
        """
        new_basis = deepcopy(current_basis)
        all_edges = {edge.edge_id for edge in graph.edges.values()}
        
        if entering_edge == leaving_edge:
            new_non_basis = all_edges - new_basis
            return new_basis, new_non_basis
        
        if leaving_edge is not None:
            new_basis.remove(leaving_edge)
            new_basis.add(entering_edge)
        
        new_non_basis = all_edges - new_basis
        return new_basis, new_non_basis
