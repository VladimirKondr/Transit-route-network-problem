from typing import List, Optional, Dict, Tuple

from network_transport.solver.utils import StepType

from ..models.graph import Graph
from .solver_base import SolutionState, TransportSolverBase
from .strategies import (
    InitializationStrategy,
    PhaseOneInitializer,
    PotentialCalculationStrategy,
    PotentialCalculator,
    OptimalityCheckStrategy,
    OptimalityChecker,
    CycleFindingStrategy,
    CycleFinder,
    ThetaCalculationStrategy,
    ThetaCalculator,
    FlowUpdateStrategy,
    FlowUpdater
)


class TransportSolver(TransportSolverBase):
    """Network transport problem solver using the simplex method."""
    
    MAX_ITERATIONS = 1000
    
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
        self.graph = graph
        self.iteration = 0
        initial_state = SolutionState(step_type=StepType.INITIAL_STATE)
        self.history: List[SolutionState] = [initial_state]
        
        if initialization_strategy is None:
            self._initialization = PhaseOneInitializer(solver_factory=lambda graph, **strategies: TransportSolver(graph, **strategies))
        else:
            self._initialization = initialization_strategy
        self._potential_calculator = potential_calculator or PotentialCalculator()
        self._optimality_checker = optimality_checker or OptimalityChecker()
        self._cycle_finder = cycle_finder or CycleFinder()
        self._theta_calculator = theta_calculator or ThetaCalculator()
        self._flow_updater = flow_updater or FlowUpdater()
        
        self._current_state: SolutionState = initial_state
    
    def solve_step_by_step(self) -> None:
        states: List[SolutionState] = []
        
        self._execute_initialization()
        initial_state = self.current_state
        states.append(initial_state)
        
        while self.iteration < self.MAX_ITERATIONS:
            self._execute_potential_calculation()
            potential_state = self.current_state
            states.append(potential_state)
            
            self._execute_optimality_check()
            optimality_state = self.current_state
            states.append(optimality_state)
            
            if optimality_state.step_type == StepType.OPTIMAL:
                break
            
            self._execute_cycle_finding()
            cycle_state = self.current_state
            states.append(cycle_state)
            
            self._execute_theta_calculation()
            theta_state = self.current_state
            states.append(theta_state)
            
            self._execute_flow_update()
            update_state = self.current_state
            states.append(update_state)
            
            self.iteration += 1
        
        if self.iteration >= self.MAX_ITERATIONS:
            raise RuntimeError(f"Maximum iterations ({self.MAX_ITERATIONS}) exceeded without reaching optimal solution")
        
        self.history = states
    
    def _execute_initialization(self) -> None:
        """Execute initialization strategy to build initial basis."""
        result = self._initialization.execute(self.graph)
        
        state = SolutionState(
            step_type=StepType.INITIAL_BASIS,
            iteration=0,
            basis_edges=result.basis_edges,
            non_basis_edges=result.non_basis_edges,
            potentials={},
            deltas={},
            flows=result.flows,
            description="Initial feasible basis constructed",
            objective_value=self._calculate_objective_value(result.flows)
        )
        
        self._current_state = state
    
    def _execute_potential_calculation(self) -> None:
        """Calculate node potentials using basis tree structure."""
        assert self._current_state.basis_edges is not None
        assert self._current_state.flows is not None

        potentials = self._potential_calculator.execute(
            self.graph,
            self._current_state.basis_edges
        )
        
        state = SolutionState(
            step_type=StepType.CALCULATE_POTENTIALS,
            iteration=self.iteration,
            basis_edges=self._current_state.basis_edges,
            non_basis_edges=self._current_state.non_basis_edges,
            potentials=potentials,
            deltas={},
            flows=self._current_state.flows,
            description="Node potentials calculated",
            objective_value=self._calculate_objective_value(self._current_state.flows)
        )
        
        self._current_state = state
    
    def _execute_optimality_check(self) -> None:
        """Check optimality conditions and identify entering variable."""
        assert self._current_state.non_basis_edges is not None
        assert self._current_state.potentials is not None
        assert self._current_state.flows  is not None

        result = self._optimality_checker.execute(
            self.graph,
            self._current_state.non_basis_edges,
            self._current_state.potentials,
            self._current_state.flows
        )
        
        if result.is_optimal:
            state = SolutionState(
                step_type=StepType.OPTIMAL,
                iteration=self.iteration,
                basis_edges=self._current_state.basis_edges,
                non_basis_edges=self._current_state.non_basis_edges,
                potentials=self._current_state.potentials,
                deltas=result.deltas,
                flows=self._current_state.flows,
                description="Optimal solution found",
                objective_value=self._calculate_objective_value(self._current_state.flows)
            )
        else:
            edge = result.entering_edge
            assert edge is not None
            
            direction = result.improvement_direction
            assert direction is not None

            delta = result.deltas[edge]
            
            description = (
                f"Violation detected: {edge[0]}→{edge[1]} "
                f"(Δ={delta:.2f}, {direction.upper()})"
            )
            
            state = SolutionState(
                step_type=StepType.CHECK_OPTIMALITY,
                iteration=self.iteration,
                basis_edges=self._current_state.basis_edges,
                non_basis_edges=self._current_state.non_basis_edges,
                potentials=self._current_state.potentials,
                deltas=result.deltas,
                flows=self._current_state.flows,
                entering_edge=result.entering_edge,
                improvement_direction=result.improvement_direction,
                description=description,
                objective_value=self._calculate_objective_value(self._current_state.flows)
            )
        
        self._current_state = state
    
    def _execute_cycle_finding(self) -> None:
        """Find improvement cycle in basis tree."""
        assert self._current_state.basis_edges is not None
        assert self._current_state.entering_edge is not None
        assert self._current_state.improvement_direction is not None
        assert self._current_state.flows  is not None

        cycle = self._cycle_finder.execute(
            self.graph,
            self._current_state.basis_edges,
            self._current_state.entering_edge,
            self._current_state.improvement_direction,
            self._current_state.flows
        )
        
        state = SolutionState(
            step_type=StepType.FIND_CYCLE,
            iteration=self.iteration,
            basis_edges=self._current_state.basis_edges,
            non_basis_edges=self._current_state.non_basis_edges,
            potentials=self._current_state.potentials,
            deltas=self._current_state.deltas,
            flows=self._current_state.flows,
            entering_edge=self._current_state.entering_edge,
            improvement_direction=self._current_state.improvement_direction,
            cycle=cycle,
            description=f"Improvement cycle found ({len(cycle)} edges)",
            objective_value=self._calculate_objective_value(self._current_state.flows)
        )
        
        self._current_state = state
    
    def _execute_theta_calculation(self) -> None:
        """Calculate maximum feasible flow adjustment."""
        assert self._current_state.cycle is not None
        assert self._current_state.flows is not None

        theta, leaving_edge = self._theta_calculator.execute(
            self._current_state.cycle,
            self._current_state.basis_edges
        )
        
        state = SolutionState(
            step_type=StepType.CALCULATE_THETA,
            iteration=self.iteration,
            basis_edges=self._current_state.basis_edges,
            non_basis_edges=self._current_state.non_basis_edges,
            potentials=self._current_state.potentials,
            deltas=self._current_state.deltas,
            flows=self._current_state.flows,
            entering_edge=self._current_state.entering_edge,
            leaving_edge=leaving_edge,
            improvement_direction=self._current_state.improvement_direction,
            cycle=self._current_state.cycle,
            theta=theta,
            description=f"Maximum flow adjustment: θ = {theta:.2f}",
            objective_value=self._calculate_objective_value(self._current_state.flows)
        )
        
        self._current_state = state
    
    def _execute_flow_update(self) -> None:
        """Update flows and swap basis edges."""
        assert self._current_state.cycle is not None
        assert self._current_state.theta is not None
        assert self._current_state.entering_edge is not None
        assert self._current_state.basis_edges is not None
        assert self._current_state.flows  is not None

        new_basis, new_non_basis, flows = self._flow_updater.execute(
            self.graph,
            self._current_state.cycle,
            self._current_state.theta,
            self._current_state.entering_edge,
            self._current_state.leaving_edge,
            self._current_state.basis_edges,
            self._current_state.flows
        )
        
        state = SolutionState(
            step_type=StepType.UPDATE_FLOWS,
            iteration=self.iteration,
            basis_edges=new_basis,
            non_basis_edges=new_non_basis,
            potentials={},
            deltas={},
            flows=flows,
            entering_edge=self._current_state.entering_edge,
            leaving_edge=self._current_state.leaving_edge,
            theta=self._current_state.theta,
            description="Flows updated, basis swapped",
            objective_value=self._calculate_objective_value(flows)
        )
        
        self._current_state = state
    
    def _calculate_objective_value(self, flows: Dict[Tuple[str, str], float]) -> float:
        """Calculate objective value from flows dictionary.
        
        Raises:
            ValueError: If some edge wasn't found in graph
        """
        total = 0.0
        for edge_id, flow in flows.items():
            edge = self.graph.get_edge(*edge_id)
            if edge is not None:
                total += edge.cost * flow 
            else:
                raise ValueError(f"Edge {edge_id} not found in graph")
        return total
    
    def step(self) -> None:
        if self._current_state.step_type == StepType.OPTIMAL:
            return None
        
        if self.iteration >= self.MAX_ITERATIONS:
            raise RuntimeError(f"Maximum iterations ({self.MAX_ITERATIONS}) exceeded without reaching optimal solution")
        
        if self._current_state.step_type == StepType.INITIAL_STATE:
            self._execute_initialization()
        
        elif self._current_state.step_type in [StepType.INITIAL_BASIS, StepType.UPDATE_FLOWS]:
            self._execute_potential_calculation()
        
        elif self._current_state.step_type == StepType.CALCULATE_POTENTIALS:
            self._execute_optimality_check()
        
        elif self._current_state.step_type == StepType.CHECK_OPTIMALITY:
            self._execute_cycle_finding()
        
        elif self._current_state.step_type == StepType.FIND_CYCLE:
            self._execute_theta_calculation()
        
        elif self._current_state.step_type == StepType.CALCULATE_THETA:
            self._execute_flow_update()
            self.iteration += 1

    @property
    def current_state(self) -> SolutionState:
        """Current solver state."""
        return self._current_state
