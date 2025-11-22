from typing import List, Tuple, Callable, Optional
from network_transport.solver.utils import SolutionState, StepType
from ..models.graph import Graph
from ..models.edge import EPSILON


class SolutionLogger:
    """Formats and logs solution steps to console and optional callback."""
    
    def __init__(self, graph: Graph, output_callback: Optional[Callable[[str], None]] = None):
        self.graph = graph
        self.output_callback = output_callback
        self._current_step_buffer: List[str] = []
        self._step_history: dict[int, str] = {}  # step_number -> log text
    
    def _print(self, text: str = "") -> None:
        """Print to console and accumulate in buffer."""
        print(text)
        self._current_step_buffer.append(text)
    
    def _flush_step_buffer(self, step_number: Optional[int] = None) -> None:
        """Send accumulated step output to callback and optionally save to history."""
        if self._current_step_buffer:
            full_step_text = '\n'.join(self._current_step_buffer)
            
            # Save to history if step_number provided
            if step_number is not None:
                self._step_history[step_number] = full_step_text
            
            # Send to callback
            if self.output_callback:
                self.output_callback(full_step_text)
        
        self._current_step_buffer.clear()
    
    def log_message(self, message: str) -> None:
        """Log a simple message (console + sidebar)."""
        self._current_step_buffer.clear()
        self._print(message)
        self._flush_step_buffer()
    
    def log_instructions(self) -> None:
        """Log interactive mode instructions."""
        self._current_step_buffer.clear()
        self._print("\n" + "="*70)
        self._print("INTERACTIVE MODE INSTRUCTIONS")
        self._print("="*70)
        self._print("< Prev       - Go to previous step")
        self._print("Next >       - Execute next algorithm step")
        self._print("Solve All    - Execute all remaining steps automatically")
        self._print("Reset        - Start solution from beginning")
        self._print("="*70)
        self._print("\nPress 'Next >' to start solving")
        self._flush_step_buffer()
    
    def log_solve_all_start(self) -> None:
        """Log start of automatic solution."""
        self._current_step_buffer.clear()
        self._print("\n" + "="*70)
        self._print("AUTOMATIC SOLUTION - EXECUTING ALL REMAINING STEPS")
        self._print("="*70)
        self._flush_step_buffer()
    
    def log_solve_all_complete(self, total_steps: int) -> None:
        """Log completion of automatic solution."""
        self._current_step_buffer.clear()
        self._print("\n" + "="*70)
        self._print(f"AUTOMATIC SOLUTION COMPLETE ({total_steps} steps)")
        self._print("="*70)
        self._flush_step_buffer()
    
    def log_reset(self) -> None:
        """Log solution reset."""
        self._current_step_buffer.clear()
        self._print("\n" + "="*70)
        self._print("RESET - Restarting from beginning")
        self._print("="*70)
        self._print("\nState reset. Press 'Next >' to begin solving.")
        self._flush_step_buffer()
        # Clear history on reset
        self._step_history.clear()
    
    def get_step_log(self, step_number: int) -> Optional[str]:
        """Get log for a specific step from history."""
        return self._step_history.get(step_number)
    
    def replay_step_log(self, step_number: int) -> None:
        """Replay (resend to callback) a previously logged step."""
        log_text = self._step_history.get(step_number)
        if log_text and self.output_callback:
            self.output_callback(log_text)
    
    def log_step(self, state: SolutionState, step_number: int) -> None:
        from ..solver.transport_solver import StepType
        
        # Clear buffer for new step
        self._current_step_buffer.clear()
        
        self._print("\n" + "="*70)
        self._print(f"STEP {step_number}: {self._get_step_name(state.step_type)}")
        self._print("="*70)
        
        self._print(f"Description: {state.description}")
        
        if state.step_type == StepType.INITIAL_BASIS:
            self._log_basis(state)
        elif state.step_type == StepType.CALCULATE_POTENTIALS:
            self._log_potentials(state)
        elif state.step_type == StepType.CHECK_OPTIMALITY:
            self._log_optimality_check(state)
        elif state.step_type == StepType.FIND_CYCLE:
            self._log_cycle(state)
        elif state.step_type == StepType.CALCULATE_THETA:
            self._log_theta(state)
        elif state.step_type == StepType.UPDATE_FLOWS:
            self._log_flow_update(state)
        elif state.step_type == StepType.OPTIMAL:
            self._log_optimal(state)
        
        self._print("-"*70)
        
        # Send complete step to callback and save to history
        self._flush_step_buffer(step_number)
    
    def _get_step_name(self, step_type: StepType) -> str:
        
        
        names = {
            StepType.INITIAL_BASIS: "Initial Basis Construction",
            StepType.CALCULATE_POTENTIALS: "Calculate Node Potentials",
            StepType.CHECK_OPTIMALITY: "Check Optimality Conditions",
            StepType.FIND_CYCLE: "Find Improvement Cycle",
            StepType.CALCULATE_THETA: "Calculate Maximum Flow Adjustment (θ)",
            StepType.UPDATE_FLOWS: "Update Flows and Basis",
            StepType.OPTIMAL: "Optimal Solution Found"
        }
        return names.get(step_type, step_type.value)
    
    def _log_basis(self, state: SolutionState) -> None:
        assert state.flows is not None
        assert state.basis_edges is not None
        self._print(f"\nBasis edges:")
        
        for edge_id in sorted(state.basis_edges):
            edge = self.graph.get_edge(*edge_id)
            assert edge is not None

            flow = state.flows.get(edge_id, 0.0)
            self._print(f"   {edge_id[0]} -> {edge_id[1]}: x={flow:.0f}, c={edge.cost:.0f}")
        

        assert state.non_basis_edges is not None
        self._print(f"\nNon-basis edges:")
        
        for edge_id in sorted(state.non_basis_edges):
            edge = self.graph.get_edge(*edge_id)
            assert edge is not None

            flow = state.flows.get(edge_id, 0.0)
            self._print(f"   {edge_id[0]} -> {edge_id[1]}: x={flow:.0f}, d={edge.capacity:.0f}")
    
    def _log_potentials(self, state: SolutionState) -> None:
        assert state.potentials is not None
        self._print(f"\nNode potentials:")
        for node_id in sorted(state.potentials.keys()):
            potential = state.potentials[node_id]
            self._print(f"   u[{node_id}] = {potential:.1f}")
    
    def _print_deltas(self, state: SolutionState) -> List[Tuple[str, str]]:
        """Print reduced costs and return list of violations."""
        assert state.flows is not None
        assert state.deltas is not None
        
        violations: List[Tuple[str, str]] = []
        for edge_id, delta in sorted(state.deltas.items()):
            edge = self.graph.get_edge(*edge_id)
            assert edge is not None

            flow = state.flows.get(edge_id, 0.0)
            
            is_empty = flow < EPSILON
            is_saturated = abs(flow - edge.capacity) < EPSILON
            violates = (is_empty and delta > EPSILON) or (is_saturated and delta < -EPSILON)
            
            status = "[OK]" if not violates else "[VIOLATION]"
            
            if is_empty:
                flow_state = "x=0"
                condition = "need Δ ≤ 0"
            elif is_saturated:
                flow_state = f"x={edge.capacity:.0f}"
                condition = "need Δ ≥ 0"
            else:
                flow_state = f"x={flow:.0f}"
                condition = "interior"
            
            self._print(f"   {status} {edge_id[0]} → {edge_id[1]}: Δ={delta:+.1f} [{flow_state}, {condition}]")
            
            if violates:
                violations.append(edge_id)
        
        return violations
    
    def _log_optimality_check(self, state: SolutionState) -> None:
        self._print(f"\nReduced costs (Δ) for non-basis edges:")
        violations = self._print_deltas(state)
        
        if violations:
            assert state.entering_edge is not None
            self._print(f"\nOptimality violations found: {len(violations)}")
            self._print(f"   Entering edge: {state.entering_edge[0]} → {state.entering_edge[1]}")
            self._print(f"   Direction: {state.improvement_direction}")
    
    def _log_cycle(self, state: 'SolutionState') -> None:
        if state.cycle:
            assert state.flows is not None
            self._print(f"\nImprovement cycle ({len(state.cycle)} edges):")
            for cycle_edge in state.cycle:
                edge = cycle_edge.edge
                sign_str = cycle_edge.sign
                limit = cycle_edge.theta_limit
                flow = state.flows.get(edge.edge_id, 0.0)
                self._print(f"   ({sign_str}) {edge.from_node} → {edge.to_node}: "
                           f"x={flow:.0f}, θ_limit={limit:.0f}")
    
    def _log_theta(self, state: 'SolutionState') -> None:
        if state.theta is not None:
            self._print(f"\nMaximum flow adjustment:")
            self._print(f"   θ = {state.theta:.1f}")
            
            if state.leaving_edge:
                self._print(f"   Leaving edge: {state.leaving_edge[0]} → {state.leaving_edge[1]}")
    
    def _log_flow_update(self, state: 'SolutionState') -> None:
        assert state.basis_edges is not None
        assert state.non_basis_edges is not None

        self._print(f"\nBasis update:")
        
        if state.entering_edge:
            self._print(f"   + Entering basis: {state.entering_edge[0]} → {state.entering_edge[1]}")
        
        if state.leaving_edge:
            self._print(f"   - Leaving basis: {state.leaving_edge[0]} → {state.leaving_edge[1]}")
        
        self._print(f"\nNew basis structure:")
        self._print(f"   Basis edges: {len(state.basis_edges)}")
        self._print(f"   Non-basis edges: {len(state.non_basis_edges)}")

        self._log_basis(state)

        self._print(f"Objective: Z = {state.objective_value:.2f}")
    
    def _log_optimal(self, state: 'SolutionState') -> None:
        assert state.flows is not None

        self._print(f"\nOPTIMAL SOLUTION FOUND")
        
        # Show optimality conditions (all deltas satisfied)
        if state.deltas is not None:
            self._print(f"\nReduced costs (Δ) for non-basis edges:")
            violations = self._print_deltas(state)
            if not violations:
                self._print(f"\nAll optimality conditions satisfied")
        
        self._print(f"\nFinal flows:")
        for edge_id, flow in sorted(state.flows.items()):
            if flow > 0:
                edge = self.graph.get_edge(*edge_id)
                assert edge is not None
                
                cost_total = flow * edge.cost
                self._print(f"   {edge.from_node} → {edge.to_node}: "
                            f"x={flow:.0f}, c={edge.cost:.0f}, total_cost={cost_total:.0f}")
        
        self._print(f"\nMinimum cost: Z = {state.objective_value:.2f}")
        self._print(f"Iterations: {state.iteration}")
    
    def print_instructions(self) -> None:
        """Print user instructions for interactive mode."""
        self._print("\n" + "="*70)
        self._print("INTERACTIVE MODE INSTRUCTIONS")
        self._print("="*70)
        self._print("< Prev       - Go to previous step")
        self._print("Next >       - Execute next algorithm step")
        self._print("Solve All    - Execute all remaining steps automatically")
        self._print("Reset        - Start solution from beginning")
        self._print("="*70)
        self._print("\nPress 'Next >' to start solving")
        self._print()
