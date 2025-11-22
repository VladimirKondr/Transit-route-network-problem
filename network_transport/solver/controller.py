from typing import List, Optional
from ..models.graph import Graph
from .solver_base import TransportSolverBase
from .transport_solver import TransportSolver, SolutionState, StepType


class SolverController:
    """
    Controls step-by-step execution of the transport problem solver.

    Responsibilities:
    - Maintain solution state history
    - Navigate between algorithm steps (next/prev)
    - Execute solver operations
    - Provide current state for visualization/logging
    """
    
    def __init__(self, graph: Graph, solver: Optional[TransportSolverBase] = None):
        """
        Initialize controller with graph and optional solver.
        
        Args:
            graph: Network graph with nodes and edges
            solver: Optional solver instance (creates default TransportSolver if None)
        """
        self.graph = graph
        self._initial_solver = solver
        self.solver = solver or TransportSolver(graph)
        self.states: List[SolutionState] = []
        self.current_step: int = -1  # -1 = not started
    
    def is_started(self) -> bool:
        """Check if solution process has started."""
        return self.current_step >= 0
    
    def is_solved(self) -> bool:
        """Check if optimal solution has been reached."""
        if not self.states:
            return False
        last_state = self.states[-1]
        return last_state.step_type == StepType.OPTIMAL
    
    def can_go_next(self) -> bool:
        """Check if we can execute or navigate to next step."""
        # Can navigate forward if not at the end of history
        if self.current_step < len(self.states) - 1:
            return True
        
        # Can compute new step if not solved yet
        if not self.is_solved():
            return True
        
        return False
    
    def can_go_prev(self) -> bool:
        """Check if we can navigate to previous step."""
        return self.current_step >= 0
    
    def get_current_state(self) -> SolutionState:
        """Get the current solution state."""
        if 0 <= self.current_step < len(self.states):
            return self.states[self.current_step]
        return SolutionState(step_type=StepType.INITIAL_STATE)
    
    def get_step_count(self) -> int:
        """Get the total number of computed steps."""
        return len(self.states)
    
    def next_step(self) -> None:
        """Execute or navigate to next step."""
        if not self.can_go_next():
            return None
        
        # If we're already at the last computed step, compute next
        if self.current_step >= len(self.states) - 1:
            self._execute_next_step()
            state = self.solver.current_state
            if state:
                self.states.append(state)
                self.current_step = len(self.states) - 1
        else:
            # Just navigate forward
            self.current_step += 1
    
    def prev_step(self) -> None:
        """Navigate to previous step."""
        if not self.can_go_prev():
            return None
        
        self.current_step -= 1
    
    def solve_all(self) -> None:
        """ Execute all remaining steps until optimal solution or max iterations."""
        while self.can_go_next():
            self.next_step()
            state = self.get_current_state()
            if not state or self.is_solved():
                break
    
    def reset(self) -> None:
        """Reset the solver to initial state."""
        self.states.clear()
        self.current_step = -1
        
        self.solver = self._initial_solver or TransportSolver(self.graph)
    
    def _execute_next_step(self) -> None:
        """Execute the next logical step of the algorithm."""
        self.solver.step()

