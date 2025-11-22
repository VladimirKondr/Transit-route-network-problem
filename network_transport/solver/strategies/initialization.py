from typing import Optional, Set, Tuple, List, Dict

from network_transport.solver.utils import SolutionState

from ...models.graph import Graph
from ...models.edge import EPSILON
from .base import InitializationStrategy, BasisResult

from ..solver_factory import SolverFactory


class DisjointSet:
    """Union-Find data structure for cycle detection."""
    
    def __init__(self, elements: List[str]) -> None:
        self.parent = {elem: elem for elem in elements}
    
    def find(self, x: str) -> str:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x: str, y: str) -> bool:
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return False
        
        self.parent[root_x] = root_y
        return True

class PrebuiltInitializer(InitializationStrategy):
    """Mock-initializer for setting a constant initial basis"""
    
    def __init__(self, basis: Set[Tuple[str, str]], flows: Dict[Tuple[str, str], float]):
        self.basis = basis
        self.flows = flows
            
    def execute(self, graph: Graph) -> BasisResult:
        all_edges = set(graph.edges.keys())
        non_basis = all_edges - self.basis
        return BasisResult(
            basis_edges=self.basis,
            non_basis_edges=non_basis,
            flows=self.flows
        )


class PhaseOneInitializer(InitializationStrategy):
    """
    Two-Phase Method (Phase 1) initialization strategy.
    
    Finds an initial feasible solution by solving an auxiliary problem with 
    artificial edges. The auxiliary problem guarantees a feasible solution exists
    by adding an artificial root node connected to all nodes with supply or demand.
    
    Algorithm:
    1. Create auxiliary graph with artificial root node
    2. Add artificial edges from/to root with capacity=∞, cost=1
    3. Set initial flows on artificial edges equal to |balance|
    4. Set costs of original edges to 0
    4. Run network simplex to minimize total artificial flow
    5. If optimal value > 0, problem is infeasible
    6. If optimal value = 0, extract feasible basis and flows for original problem
    """
    
    ROOT_NODE_ID = "__artificial_root__"
    ARTIFICIAL_COST = 1.0
    ORIGINAL_COST = 0.0

    def __init__(self, solver_factory: Optional[SolverFactory] = None):
        self.solver_factory = solver_factory
    
    def execute(self, graph: Graph) -> BasisResult:
        """Execute Phase 1 initialization."""
        total_balance = sum(node.balance for node in graph.nodes.values())
        if abs(total_balance) > EPSILON:
            raise ValueError(
                f"Invalid problem: Total balance is not zero ({total_balance}). "
                "Sum of supply must equal sum of demand."
            )
        
        aux_graph = self._create_auxiliary_graph(graph)
        
        initial_basis, initial_flows = self._setup_initial_state(graph)

        if not self.solver_factory:
            from ..transport_solver import TransportSolver
            factory = TransportSolver
        else:
            factory = self.solver_factory

        solver = factory(
            aux_graph,
            initialization_strategy=PrebuiltInitializer(initial_basis, initial_flows)
        )
        try:
            solver.solve_step_by_step()
        except:
            raise RuntimeError("[ERROR] First phase doesn't have a solution")

        final_state: SolutionState = solver.current_state
        
        return self._extract_original_solution(graph, final_state)
    
    def _create_auxiliary_graph(self, graph: Graph) -> Graph:
        """
        Create auxiliary graph for Phase 1.
        """
        aux_graph = Graph()
        
        aux_graph.add_node(self.ROOT_NODE_ID, balance=0.0)
        
        for node_id, node in sorted(graph.nodes.items()):
            aux_graph.add_node(node_id, balance=node.balance)
        
        for _, edge in sorted(graph.edges.items()):
            aux_graph.add_edge(
                edge.from_node,
                edge.to_node,
                cost=self.ORIGINAL_COST,
                capacity=edge.capacity
            )
        
        # Add edges to all nodes (from node if node is source)
        for node_id, node in sorted(graph.nodes.items()):
            if node.balance > EPSILON:
                aux_graph.add_edge(
                    node_id,
                    self.ROOT_NODE_ID,
                    cost=self.ARTIFICIAL_COST,
                    capacity=float('inf')
                )
            else:
                aux_graph.add_edge(
                    self.ROOT_NODE_ID,
                    node_id,
                    cost=self.ARTIFICIAL_COST,
                    capacity=float('inf')
                )
        
        return aux_graph
    
    def _setup_initial_state(self, graph: Graph) -> Tuple[Set[Tuple[str, str]], Dict[Tuple[str, str], float]]:
        """
        Set up initial basis and flows for Phase 1.
        """
        basis: Set[Tuple[str, str]] = set()
        flows: Dict[Tuple[str, str], float] = {}
        
        for edge_id in sorted(graph.edges.keys()):
            flows[edge_id] = 0.0
            
        for node_id, node in sorted(graph.nodes.items()):
            if node.balance > EPSILON:
                edge_id = (node_id, self.ROOT_NODE_ID)
                basis.add(edge_id)
                flows[edge_id] = node.balance
            else:
                edge_id = (self.ROOT_NODE_ID, node_id)
                basis.add(edge_id)
                
                if node.balance < -EPSILON:
                    flows[edge_id] = abs(node.balance)
                else:
                    flows[edge_id] = 0.0
        
        return basis, flows
    
    def _extract_original_solution(self, graph: Graph, final_state: SolutionState) -> BasisResult:
        """
        Extract feasible solution for original problem from auxiliary solution.
        
        Args:
            graph: Original graph
            final_state: Final state from auxiliary problem solver
            
        Returns:
            BasisResult for original problem
            
        Raises:
            ValueError: If problem is infeasible
        """
        if final_state.flows is None:
            raise ValueError("Solver did not produce a solution")
        
        artificial_flow = 0.0
        for edge_id, flow in final_state.flows.items():
            if self.ROOT_NODE_ID in edge_id:
                artificial_flow += flow
        
        if artificial_flow > EPSILON:
            raise ValueError(
                f"Problem is infeasible. Total artificial flow: {artificial_flow:.6f}"
            )
        
        original_edges = set(graph.edges.keys())
        basis_edges: Set[Tuple[str, str]] = set()
        flows: Dict[Tuple[str, str], float] = {}
        
        for edge_id in original_edges:
            flows[edge_id] = final_state.flows.get(edge_id, 0.0)
        
        if final_state.basis_edges:
            for edge_id in final_state.basis_edges:
                if self.ROOT_NODE_ID not in edge_id:
                    basis_edges.add(edge_id)
        
        basis_edges = self._rebuild_basis(graph, basis_edges, flows)
        
        non_basis_edges = original_edges - basis_edges
        
        return BasisResult(
            basis_edges=basis_edges,
            non_basis_edges=non_basis_edges,
            flows=flows
        )
    
    def _rebuild_basis(
        self, 
        graph: Graph, 
        partial_basis: Set[Tuple[str, str]], 
        flows: Dict[Tuple[str, str], float]
    ) -> Set[Tuple[str, str]]:
        """
        Rebuild a complete spanning tree basis from a partial basis.
        
        If the partial basis doesn't form a complete spanning tree,
        add edges from the graph until we have a valid tree structure.
        
        Args:
            graph: Original graph
            partial_basis: Partial set of basis edges
            flows: Current flow values
            
        Returns:
            Complete spanning tree basis
        """
        num_nodes = len(graph.nodes)
        required_size = num_nodes - 1

        node_ids = list(graph.nodes.keys())
        dsu = DisjointSet(node_ids)
        basis: Set[Tuple[str, str]] = set()

        def try_add_candidate(candidate_edge_id: Tuple[str, str]) -> None:
            from_node, to_node = candidate_edge_id
            if dsu.union(from_node, to_node):
                basis.add(candidate_edge_id)
        
        for edge_id in partial_basis:
            try_add_candidate(edge_id)
        
        if len(basis) < required_size:
            candidate_edges = [
                edge_id for edge_id in graph.edges.keys()
                if edge_id not in basis and flows.get(edge_id, 0.0) > EPSILON
            ]
            
            for edge_id in candidate_edges:
                if len(basis) >= required_size:
                    break
                try_add_candidate(edge_id)
        
        if len(basis) < required_size:
            for edge_id in graph.edges.keys():
                if len(basis) >= required_size:
                    break
                if edge_id not in basis:
                    try_add_candidate(edge_id)
        
        if len(basis) < required_size:
            raise ValueError(
                "Original graph is not connected. Cannot build a spanning tree basis. "
                f"Found {len(basis)} edges, required {required_size}."
            )
        
        return basis