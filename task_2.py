from network_transport import Graph, TransportSolver, SolverController
from network_transport.solver.strategies.initialization import PrebuiltInitializer
from network_transport.ui import InteractiveSession, LayoutContext
from typing import Set, Tuple, Dict


def create_capacitated_network() -> Graph:
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


def print_network_info(graph: Graph) -> None:
    print("Nodes:")
    for node in graph.nodes.values():
        node_type = node.node_type.value.capitalize()
        print(f"  {node.id}: balance={node.balance:+3d} ({node_type})")
    print()
    
    print("Edges (with capacity constraints):")
    for edge in graph.edges.values():
        capacity_str = f"{edge.capacity:.0f}" if edge.capacity != float('inf') else "∞"
        print(f"  {edge.from_node} → {edge.to_node}: "
              f"cost={edge.cost:.0f}, capacity={capacity_str}")
    print()


def create_initial_plan() -> Tuple[Set[Tuple[str, str]], Dict[Tuple[str, str], float]]:
    basis_edges: Set[Tuple[str, str]] = {
        ("1", "2"),
        ("1", "5"),
        ("3", "4"),
        ("5", "8"),
        ("6", "8"),
        ("7", "3"),
        ("8", "3"),
    }
    
    flows: Dict[Tuple[str, str], float] = {
        ("1", "2"): 18.0,
        ("1", "5"): 22.0,
        ("3", "4"): 40.0,
        ("5", "8"): 2.0,
        ("6", "8"): 23.0,
        ("7", "3"): 40.0,
        ("8", "3"): 5.0,
        ("2", "3"): 45.0,
        ("2", "7"): 40.0,
        ("8", "4"): 20.0,
    }
    
    return basis_edges, flows


def main() -> None:
    """Run interactive solution with predefined initial plan."""
    print("\n" + "=" * 70)
    print("Network Planning Problem (Capacitated) - With Initial Plan")
    print("=" * 70)
    print()
    
    graph = create_capacitated_network()
    
    print_network_info(graph)
    
    print("Initial Plan:")
    print("  Basis edges: 7")
    print("  Non-basis (saturated): 3")
    print()
    
    basis_edges, flows = create_initial_plan()
    
    initialization_strategy = PrebuiltInitializer(basis_edges, flows)
    solver = TransportSolver(graph=graph, initialization_strategy=initialization_strategy)
    controller = SolverController(graph, solver=solver)
    
    layout = LayoutContext()
    session = InteractiveSession(graph, layout, controller, show_console_in_sidebar=True)
    
    print("Starting interactive solver...")
    session.setup_and_run()


if __name__ == "__main__":
    main()
