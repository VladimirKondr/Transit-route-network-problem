from typing import List, Tuple
from network_transport.solver.utils import SolutionState, StepType
from ..models.graph import Graph
from ..models.edge import EPSILON


class SolutionLogger:
    """Formats and logs solution steps to console."""
    
    def __init__(self, graph: Graph):
        self.graph = graph
    
    def log_step(self, state: SolutionState, step_number: int) -> None:
        from ..solver.transport_solver import StepType
        
        print("\n" + "="*70)
        print(f"STEP {step_number}: {self._get_step_name(state.step_type)}")
        print("="*70)
        
        print(f"Description: {state.description}")
        
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
        
        print("-"*70)
    
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
        print(f"\nBasis edges:")
        
        for edge_id in sorted(state.basis_edges):
            edge = self.graph.get_edge(*edge_id)
            assert edge is not None

            flow = state.flows.get(edge_id, 0.0)
            print(f"   {edge_id[0]} -> {edge_id[1]}: x={flow:.0f}, c={edge.cost:.0f}")
        

        assert state.non_basis_edges is not None
        print(f"\nNon-basis edges:")
        
        for edge_id in sorted(state.non_basis_edges):
            edge = self.graph.get_edge(*edge_id)
            assert edge is not None

            flow = state.flows.get(edge_id, 0.0)
            print(f"   {edge_id[0]} -> {edge_id[1]}: x={flow:.0f}, d={edge.capacity:.0f}")
    
    def _log_potentials(self, state: SolutionState) -> None:
        assert state.potentials is not None
        print(f"\nNode potentials:")
        for node_id in sorted(state.potentials.keys()):
            potential = state.potentials[node_id]
            print(f"   u[{node_id}] = {potential:.1f}")
    
    def _log_optimality_check(self, state: SolutionState) -> None:
        assert state.flows is not None
        assert state.deltas is not None
        
        print(f"\nReduced costs (Δ) for non-basis edges:")
        
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
            
            print(f"   {status} {edge_id[0]} → {edge_id[1]}: Δ={delta:+.1f} [{flow_state}, {condition}]")
            
            if violates:
                violations.append(edge_id)
        
        if violations:
            assert state.entering_edge is not None
            print(f"\nOptimality violations found: {len(violations)}")
            print(f"   Entering edge: {state.entering_edge[0]} → {state.entering_edge[1]}")
            print(f"   Direction: {state.improvement_direction}")
    
    def _log_cycle(self, state: 'SolutionState') -> None:
        if state.cycle:
            assert state.flows is not None
            print(f"\nImprovement cycle ({len(state.cycle)} edges):")
            for cycle_edge in state.cycle:
                edge = cycle_edge.edge
                sign_str = cycle_edge.sign
                limit = cycle_edge.theta_limit
                flow = state.flows.get(edge.edge_id, 0.0)
                print(f"   ({sign_str}) {edge.from_node} → {edge.to_node}: "
                      f"x={flow:.0f}, θ_limit={limit:.0f}")
    
    def _log_theta(self, state: 'SolutionState') -> None:
        if state.theta is not None:
            print(f"\nMaximum flow adjustment:")
            print(f"   θ = {state.theta:.1f}")
            
            if state.leaving_edge:
                print(f"   Leaving edge: {state.leaving_edge[0]} → {state.leaving_edge[1]}")
    
    def _log_flow_update(self, state: 'SolutionState') -> None:
        assert state.basis_edges is not None
        assert state.non_basis_edges is not None

        print(f"\nBasis update:")
        
        if state.entering_edge:
            print(f"   ➕ Entering basis: {state.entering_edge[0]} → {state.entering_edge[1]}")
        
        if state.leaving_edge:
            print(f"   ➖ Leaving basis: {state.leaving_edge[0]} → {state.leaving_edge[1]}")
        
        print(f"\nNew basis structure:")
        print(f"   Basis edges: {len(state.basis_edges)}")
        print(f"   Non-basis edges: {len(state.non_basis_edges)}")

        self._log_basis(state)

        print(f"Objective: Z = {state.objective_value:.2f}")
    
    def _log_optimal(self, state: 'SolutionState') -> None:
        assert state.flows is not None

        print(f"\nOPTIMAL SOLUTION FOUND")
        print(f"\nFinal flows:")
        for edge_id, flow in sorted(state.flows.items()):
            if flow > 0:
                edge = self.graph.get_edge(*edge_id)
                assert edge is not None
                
                cost_total = flow * edge.cost
                print(f"   {edge.from_node} → {edge.to_node}: "
                      f"x={flow:.0f}, c={edge.cost:.0f}, total_cost={cost_total:.0f}")
        
        print(f"\nMinimum cost: Z = {state.objective_value:.2f}")
        print(f"Iterations: {state.iteration}")
    
    def print_instructions(self) -> None:
        """Print user instructions for interactive mode."""
        print("\n" + "="*70)
        print("INTERACTIVE MODE INSTRUCTIONS")
        print("="*70)
        print("< Prev       - Go to previous step")
        print("Next >       - Execute next algorithm step")
        print("Solve All    - Execute all remaining steps automatically")
        print("Reset        - Start solution from beginning")
        print("="*70)
        print("\nPress 'Next >' to start solving")
        print()
