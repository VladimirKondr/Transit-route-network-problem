from abc import ABC, abstractmethod
from typing import Dict, Set, Tuple, List, Optional

from network_transport.solver.utils import BasisResult, CycleEdge, OptimalityResult

from ...models.graph import Graph


# Initialization Strategy

class InitializationStrategy(ABC):
    """Interface for finding initial feasible basis and flows."""
    
    @abstractmethod
    def execute(self, graph: Graph) -> BasisResult:
        """
        Find initial feasible solution.
        
        Args:
            graph: Network graph with nodes and edges
            
        Returns:
            BasisResult with initial basis, non-basis edges, and flows
            
        Raises:
            ValueError: If no feasible solution exists
        """
        pass


# Potential Calculation Strategy

class PotentialCalculationStrategy(ABC):
    """Interface for calculating node potentials."""
    
    @abstractmethod
    def execute(
        self, 
        graph: Graph, 
        basis_edges: Set[Tuple[str, str]]
    ) -> Dict[str, float]:
        """
        Calculate node potentials using basis tree structure.
        
        For each basis edge (i,j): potential[j] = potential[i] + cost[i,j]
        
        Args:
            graph: Network graph (read-only)
            basis_edges: Current basis edges forming spanning tree
            
        Returns:
            Dictionary mapping node_id to potential value
        """
        pass


# Optimality Checking Strategy

class OptimalityCheckStrategy(ABC):
    """Interface for checking optimality conditions and selecting entering variable."""
    
    @abstractmethod
    def execute(
        self,
        graph: Graph,
        non_basis_edges: Set[Tuple[str, str]],
        potentials: Dict[str, float],
        flows: Dict[Tuple[str, str], float]
    ) -> OptimalityResult:
        """
        Computes reduced costs (deltas) for non-basis edges:
        - delta[i,j] = cost[i,j] - (potential[j] - potential[i])
        
        Checks for violations:
        - At lower bound (flow=0): delta < 0 means can increase flow
        - At upper bound (flow=capacity): delta > 0 means can decrease flow
        
        Args:
            graph: Network graph (read-only)
            non_basis_edges: Non-basis edges to check
            potentials: Current node potentials
            flows: Current flow values
            
        Returns:
            OptimalityResult with optimality status and entering edge if not optimal
        """
        pass


# Cycle Finding Strategy

class CycleFindingStrategy(ABC):
    """Interface for finding cycle in basis tree."""
    
    @abstractmethod
    def execute(
        self,
        graph: Graph,
        basis_edges: Set[Tuple[str, str]],
        entering_edge: Tuple[str, str],
        direction: str,
        flows: Dict[Tuple[str, str], float]
    ) -> List[CycleEdge]:
        """
        Find cycle formed when entering edge is added to basis tree.
        
        The cycle consists of:
        - The entering edge (non-basis)
        - Tree path connecting the endpoints (basis edges)
        
        Each edge is labeled with:
        - Sign: "+" (flow increases) or "-" (flow decreases)
        - Theta limit: maximum flow change without violating constraints
        
        Args:
            graph: Network graph (read-only)
            basis_edges: Current basis edges
            entering_edge: Edge to add to basis
            direction: "increase" or "decrease" flow direction
            flows: Current flow values
            
        Returns:
            List of CycleEdge objects forming the improvement cycle
        """
        pass


# Theta Calculation Strategy

class ThetaCalculationStrategy(ABC):
    """Interface for calculating maximum feasible flow adjustment."""
    
    @abstractmethod
    def execute(
        self, 
        cycle: List[CycleEdge],
        basis_edges: Optional[Set[Tuple[str, str]]] = None
    ) -> Tuple[float, Optional[Tuple[str, str]]]:
        """
        Calculate maximum flow adjustment and identify leaving edge.
        
        Theta is the minimum theta_limit across all cycle edges:
        - theta = min{theta_limit[i] : for all edges in cycle}
        
        The edge(s) that achieve this minimum become candidates for leaving.
        Uses tie-breaking rules to select one.
        
        Args:
            cycle: Cycle with edges and limits
            basis_edges: Current basis edges (for tie-breaking)
            
        Returns:
            Tuple of (theta_value, leaving_edge_id)
            leaving_edge_id is None only if theta = 0 (degenerate case)
        """
        pass


# Flow Update Strategy

class FlowUpdateStrategy(ABC):
    """Interface for updating flows and basis after cycle adjustment."""
    
    @abstractmethod
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
        """
        Update flows along cycle and swap basis edges.
        
        Flow adjustment:
        - For edges with sign "+": flow += theta
        - For edges with sign "-": flow -= theta
        
        Basis update:
        - Remove leaving edge from basis
        - Add entering edge to basis
        - Update non-basis set accordingly
        
        Special case: If entering_edge = leaving_edge (degeneracy),
        basis remains unchanged.
        
        Args:
            graph: Network graph (read-only)
            cycle: Improvement cycle
            theta: Flow adjustment amount
            entering_edge: Edge entering basis
            leaving_edge: Edge leaving basis (None if degenerate)
            current_basis: Current basis edges
            current_flows: Current flow values
            
        Returns:
            Tuple of (new_basis_edges, new_non_basis_edges, new_flows)
        """
        pass
