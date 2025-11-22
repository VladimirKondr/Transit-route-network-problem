from typing import Optional

from network_transport.solver.utils import StepType
from ..models.node import Node
from ..models.edge import Edge, EPSILON
from ..solver.transport_solver import SolutionState


class NodeViewModel:
    def __init__(self, node: Node, state: Optional[SolutionState] = None):
        """
        Create ViewModel wrapping a node with optional solution state.
        
        Args:
            node: Node model (problem data)
            state: Optional SolutionState (dynamic solver state)
        """
        self._node = node
        self._state = state
    
    @property
    def id(self) -> str:
        return self._node.id
    
    @property
    def balance(self) -> float:
        return self._node.balance
    
    @property
    def node_type(self):
        return self._node.node_type
    
    @property
    def potential(self) -> Optional[float]:
        if self._state and \
            self._state.step_type != StepType.INITIAL_STATE and \
            self._state.potentials and \
            self._node.id in self._state.potentials:

            assert self._state.potentials is not None
            return self._state.potentials[self._node.id]
        return None
    
    def __repr__(self) -> str:
        return f"NodeViewModel({self._node.id}, balance={self.balance}, potential={self.potential})"
    
    def __str__(self) -> str:
        return f"Node {self.id} [{self.node_type.value}]: b={self.balance}, u={self.potential}"


class EdgeViewModel:
    def __init__(self, edge: Edge, state: Optional[SolutionState] = None):
        """
        Create ViewModel wrapping an edge with optional solution state.
        
        Args:
            edge: Immutable Edge model (problem data)
            state: Optional SolutionState (dynamic solver state)
        """
        self._edge = edge
        self._state = state
    
    @property
    def from_node(self) -> str:
        return self._edge.from_node
    
    @property
    def to_node(self) -> str:
        return self._edge.to_node
    
    @property
    def cost(self) -> float:
        return self._edge.cost
    
    @property
    def capacity(self) -> float:
        return self._edge.capacity
    
    @property
    def edge_id(self) -> tuple[str, str]:
        return self._edge.edge_id
    
    @property
    def flow(self) -> float:
        if self._state and \
            self._state.step_type != StepType.INITIAL_STATE and \
            self._state.flows and \
            self._edge.edge_id in self._state.flows:

            return self._state.flows[self._edge.edge_id]
        return 0.0
    
    @property
    def is_basis(self) -> bool:
        if self._state and self._state.step_type != StepType.INITIAL_STATE:
            assert self._state.basis_edges is not None
            return self._edge.edge_id in self._state.basis_edges
        return False
    
    @property
    def delta(self) -> Optional[float]:
        if self._state and \
            self._state.step_type != StepType.INITIAL_STATE and \
            self._state.deltas and \
            self._edge.edge_id in self._state.deltas:
            
            assert self._state.deltas is not None
            return self._state.deltas[self._edge.edge_id]
        return None
    
    @property
    def is_saturated(self) -> bool:
        return self.flow >= self.capacity - EPSILON
    
    @property
    def is_empty(self) -> bool:
        return self.flow <= EPSILON
    
    @property
    def residual_capacity(self) -> float:
        return self.capacity - self.flow
    
    @property
    def cycle_sign(self) -> Optional[str]:
        if self._state and self._state.step_type != StepType.INITIAL_STATE and self._state.cycle:
            for cycle_edge in self._state.cycle:
                if cycle_edge.edge.edge_id == self._edge.edge_id:
                    return cycle_edge.sign
        return None
    
    def violates_optimality(self) -> bool:
        if self.is_basis or self.delta is None:
            return False
        
        if self.is_empty:
            return self.delta > EPSILON
        elif self.is_saturated:
            return self.delta < -EPSILON
        
        return False
    
    def get_optimality_violation(self) -> Optional[tuple[float, str]]:
        if self.is_basis or self.delta is None:
            return None
        
        if self.is_empty and self.delta > EPSILON:
            return (self.delta, "increase")
        elif self.is_saturated and self.delta < -EPSILON:
            return (abs(self.delta), "decrease")
        
        return None
    
    def __repr__(self) -> str:
        basis = "basis" if self.is_basis else "non-basis"
        return f"EdgeViewModel({self.from_node}->{self.to_node}, c={self.cost}, x={self.flow}/{self.capacity}, {basis})"
    
    def __str__(self) -> str:
        basis = "[B]" if self.is_basis else "[NB]"
        delta_str = f", Δ={self.delta:.2f}" if self.delta is not None else ""
        return f"{basis} {self.from_node}→{self.to_node}: x={self.flow}, c={self.cost}, d={self.capacity}{delta_str}"
