from abc import ABC, abstractmethod
from typing import Optional

from network_transport.solver.utils import SolutionState

from ..models.graph import Graph
from .strategies import (
    InitializationStrategy,
    PotentialCalculationStrategy,
    OptimalityCheckStrategy,
    CycleFindingStrategy,
    ThetaCalculationStrategy,
    FlowUpdateStrategy,
)


class TransportSolverBase(ABC):
    """
    Abstract base class for network transport problem solvers.
    
    This interface defines the contract that all solver implementations must follow.
    Allows for dependency injection and testing with mock implementations.
    """
    
    def __init__(
        self,
        graph: Graph,
        initialization_strategy: Optional[InitializationStrategy] = None,
        potential_calculator: Optional[PotentialCalculationStrategy] = None,
        optimality_checker: Optional[OptimalityCheckStrategy] = None,
        cycle_finder: Optional[CycleFindingStrategy] = None,
        theta_calculator: Optional[ThetaCalculationStrategy] = None,
        flow_updater: Optional[FlowUpdateStrategy] = None
    ) -> None:
        """
        Initialize solver with graph and strategies.

        Args:
            graph: Network graph with nodes and edges
            initialization_strategy: Strategy for building initial basis
            potential_calculator: Strategy for computing node potentials
            optimality_checker: Strategy for checking KKT conditions
            cycle_finder: Strategy for finding improvement cycles
            theta_calculator: Strategy for computing max flow adjustment
            flow_updater: Strategy for updating flows and basis
        """
        self.graph = graph
    
    @abstractmethod
    def solve_step_by_step(self) -> None:
        """
        Execute complete solution algorithm from start to finish.
        
        Runs all steps of the network simplex method until optimal solution
        is found or maximum iterations are reached.
        
        Raises:
            RuntimeError: If maximum iterations exceeded
            ValueError: If problem is infeasible
        """
        pass
    
    @abstractmethod
    def step(self) -> None:
        """
        Execute next algorithm step based on current state.
        
        This is the public interface for step-by-step execution.
        Implements state machine logic to transition between algorithm phases.
        
        State transitions:
        - INITIAL_STATE → INITIAL_BASIS (initialization)
        - INITIAL_BASIS → CALCULATE_POTENTIALS
        - CALCULATE_POTENTIALS → CHECK_OPTIMALITY
        - CHECK_OPTIMALITY → FIND_CYCLE (if not optimal) or OPTIMAL
        - FIND_CYCLE → CALCULATE_THETA
        - CALCULATE_THETA → UPDATE_FLOWS
        - UPDATE_FLOWS → CALCULATE_POTENTIALS
        
        Raises:
            RuntimeError: If maximum iterations exceeded
        """
        pass
    
    @property
    @abstractmethod
    def current_state(self) -> SolutionState:
        """
        Get current solver state.
        
        Returns:
            SolutionState object containing basis, flows, potentials, etc.
        """
        pass
