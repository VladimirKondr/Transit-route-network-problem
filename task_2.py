from network_transport import Graph, run_interactive_demo


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


def main() -> None:
    """Run interactive solution using utility function."""
    graph = create_capacitated_network()
    
    run_interactive_demo(
        graph,
        title="Network Planning Problem (Capacitated)",
        info_printer=print_network_info
    )


if __name__ == "__main__":
    main()
