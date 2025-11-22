from network_transport import Graph, TransportSolver, SolverController
from network_transport.solver.strategies import PhaseOneInitializer, InitializationStrategy
from network_transport.solver.strategies.initialization import PrebuiltInitializer
from network_transport.ui import InteractiveSession, LayoutContext
from network_transport.solver.utils import BasisResult, SolutionState
from typing import Set, Tuple, Dict


def create_railway_network() -> Graph:
    graph = Graph()
    
    stations = [
        ("A1", 4), ("A2", -5), ("A3", 0), ("A4", 7),
        ("A5", 4), ("A6", 0), ("A7", -10),
    ]
    
    for station_id, balance in stations:
        graph.add_node(station_id, balance=balance)
    
    routes = [
        ("A1", "A2", 3), ("A1", "A3", 9), ("A2", "A5", 4), ("A2", "A6", 10),
        ("A3", "A2", 2), ("A3", "A6", 7), ("A4", "A1", 5), ("A4", "A3", 4),
        ("A5", "A6", 2), ("A5", "A7", 2), ("A6", "A4", 6), ("A6", "A7", 6),
    ]
    
    for from_st, to_st, cost in routes:
        graph.add_edge(from_st, to_st, cost=cost, capacity=float("inf"))
    
    return graph


class PhaseOneHelper:
    
    def __init__(self):
        self.initializer = PhaseOneInitializer()
    
    def create_auxiliary_graph(self, graph: Graph) -> Graph:
        return self.initializer._create_auxiliary_graph(graph) # pyright: ignore[reportPrivateUsage]
    
    def create_initial_basis(self, graph: Graph) -> Tuple[Set[Tuple[str, str]], Dict[Tuple[str, str], float]]:
        return self.initializer._setup_initial_state(graph) # pyright: ignore[reportPrivateUsage]
    
    def extract_basis_for_phase2(self, original_graph: Graph, aux_final_state: SolutionState) -> BasisResult:
        return self.initializer._extract_original_solution(original_graph, aux_final_state) # pyright: ignore[reportPrivateUsage]

def print_phase_header(phase_num: int, title: str) -> None:
    print("\n" + "=" * 70)
    print(f"PHASE {phase_num}: {title}")
    print("=" * 70)


def run_phase(
    graph: Graph, 
    initialization_strategy: InitializationStrategy,
    phase_name: str
) -> SolverController:
    solver = TransportSolver(graph=graph, initialization_strategy=initialization_strategy)
    controller = SolverController(graph, solver=solver)
    layout = LayoutContext()
    session = InteractiveSession(graph, layout, controller)
    
    print(f"\nStarting {phase_name}...")

    session.setup_and_run()
    return controller


def main() -> None:
    print("\n" + "=" * 70)
    print("Two-Phase - Railway Transportation Problem")
    print("=" * 70)
    
    original_graph = create_railway_network()
    helper = PhaseOneHelper()
    
    print_phase_header(1, "Find Initial Feasible Solution")
    
    aux_graph = helper.create_auxiliary_graph(original_graph)
    initial_basis, initial_flows = helper.create_initial_basis(original_graph)
    
    aux_controller = run_phase(
        aux_graph,
        PrebuiltInitializer(initial_basis, initial_flows),
        "Phase 1"
    )
    
    if not aux_controller.is_solved():
        print("\n Phase 1 not completed. Cannot proceed to Phase 2.")
        return
    
    final_aux_state = aux_controller.get_current_state()

    phase2_result = helper.extract_basis_for_phase2(original_graph, final_aux_state)
    
    print_phase_header(2, "Optimize Transportation Cost")
    
    phase2_controller = run_phase(
        original_graph,
        PrebuiltInitializer(phase2_result.basis_edges, phase2_result.flows),
        "Phase 2"
    )
    
    if phase2_controller.is_solved():
        final_state = phase2_controller.get_current_state()
        
        print("\n" + "=" * 70)
        print("SOLUTION SUMMARY")
        print("=" * 70)
        print(f"Phase 1 iterations:  {final_aux_state.iteration + 1}")
        print(f"Phase 2 iterations:  {final_state.iteration + 1}")
        print(f"Total iterations:    {final_aux_state.iteration + final_state.iteration + 2}")
        print(f"\nOptimal cost:        {final_state.objective_value:.2f}")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
