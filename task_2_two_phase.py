from network_transport import Graph, TransportSolver, SolverController
from network_transport.solver.strategies import PhaseOneInitializer, InitializationStrategy
from network_transport.solver.strategies.initialization import PrebuiltInitializer
from network_transport.ui import InteractiveSession, LayoutContext
from network_transport.solver.utils import BasisResult, SolutionState
from typing import Set, Tuple, Dict


def create_railway_network() -> Graph:
    graph = Graph()
    
    nodes_config = [
        ("1", +40, "Source"),
        ("2", +67, "Source"),
        ("3", -50, "Sink"),
        ("4", -60, "Sink"),
        ("5", -20, "Sink"),
        ("6", +23, "Source"),
        ("7", 0, "Transit"),
        ("8", 0, "Transit"),
    ]
    
    for node_id, balance, _ in nodes_config:
        graph.add_node(node_id, balance=balance)
    
    edges_config = [
        ("1", "2", 4, 35),
        ("1", "5", 6, 50),
        ("2", "3", 9, 45),
        ("2", "7", 8, 40),
        ("3", "4", 7, 45),
        ("4", "6", 5, 20),
        ("5", "6", 6, 20),
        ("5", "8", 11, 20),
        ("6", "8", 12, 41),
        ("7", "1", 15, 10),
        ("7", "3", 3, 40),
        ("7", "5", 7, 15),
        ("8", "3", 8, 15),
        ("8", "4", 16, 20),
        ("8", "7", 19, 10),
    ]
    
    for from_node, to_node, cost, capacity in edges_config:
        graph.add_edge(from_node, to_node, cost=cost, capacity=capacity)
    
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


def create_phase_info_printer(phase_num: int, phase_name: str):
    """Create info printer function for sidebar."""
    def info_printer(graph: Graph) -> None:
        from network_transport.models.edge import EPSILON
        
        print(f"╔{'═' * 48}╗")
        print(f"║ {'PHASE ' + str(phase_num) + ': ' + phase_name:^46} ║")
        print(f"╠{'═' * 48}╣")
        
        # Network info
        print(f"║ {'Network Structure':^46} ║")
        print(f"╟{'─' * 48}╢")
        print(f"║  Nodes: {len(graph.nodes):<39} ║")
        print(f"║  Edges: {len(graph.edges):<39} ║")
        
        # Calculate supply/demand
        total_supply = sum(n.balance for n in graph.nodes.values() if n.balance > EPSILON)
        total_demand = -sum(n.balance for n in graph.nodes.values() if n.balance < -EPSILON)
        
        print(f"║  Supply: {total_supply:<38.0f} ║")
        print(f"║  Demand: {total_demand:<38.0f} ║")
        
        # Phase-specific info
        print(f"╟{'─' * 48}╢")
        if phase_num == 1:
            print(f"║ {'Objective':^46} ║")
            print(f"╟{'─' * 48}╢")
            print(f"║  Minimize artificial flow              ║")
            print(f"║  Find feasible basis                   ║")
        else:
            print(f"║ {'Objective':^46} ║")
            print(f"╟{'─' * 48}╢")
            print(f"║  Minimize total transportation cost    ║")
            print(f"║  Using feasible basis from Phase 1     ║")
        
        print(f"╚{'═' * 48}╝")
    
    return info_printer


def run_phase(
    graph: Graph, 
    initialization_strategy: InitializationStrategy,
    phase_name: str,
    phase_num: int
) -> SolverController:
    solver = TransportSolver(graph=graph, initialization_strategy=initialization_strategy)
    controller = SolverController(graph, solver=solver)
    layout = LayoutContext()
    
    # Create info printer for this phase
    info_printer = create_phase_info_printer(phase_num, phase_name)
    
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
