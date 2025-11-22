import matplotlib
matplotlib.use('WebAgg')

matplotlib.rcParams['webagg.open_in_browser'] = True
matplotlib.rcParams['webagg.port'] = 8988
matplotlib.rcParams['webagg.address'] = '127.0.0.1'

matplotlib.rcParams['figure.dpi'] = 80
matplotlib.rcParams['savefig.dpi'] = 100

from network_transport import Graph, run_interactive_demo

def create_railway_network() -> Graph:
    graph = Graph()
    
    stations = [
        ("A1", 4, "Source"),
        ("A2", -5, "Sink"),
        ("A3", 0, "Transit"),
        ("A4", 7, "Source"),
        ("A5", 4, "Source"),
        ("A6", 0, "Transit"),
        ("A7", -10, "Sink"),
    ]
    
    for station_id, balance, _ in stations:
        graph.add_node(station_id, balance=balance)
    
    routes = [
        ("A1", "A2", 3, float("inf")),
        ("A1", "A3", 9, float("inf")),
        ("A2", "A5", 4, float("inf")),
        ("A2", "A6", 10, float("inf")),
        ("A3", "A2", 2, float("inf")),
        ("A3", "A6", 7, float("inf")),
        ("A4", "A1", 5, float("inf")),
        ("A4", "A3", 4, float("inf")),
        ("A5", "A6", 2, float("inf")),
        ("A5", "A7", 2, float("inf")),
        ("A6", "A4", 6, float("inf")),
        ("A6", "A7", 6, float("inf")),
    ]
    
    for from_st, to_st, cost, capacity in routes:
        graph.add_edge(from_st, to_st, cost=cost, capacity=capacity)
    
    return graph


def print_network_info(graph: Graph) -> None:
    print("Stations:")
    for node in graph.nodes.values():
        node_type = node.node_type.value.capitalize()
        print(f"  {node.id}: balance={node.balance:+3d} ({node_type})")
    print()
    
    print("Routes:")
    for edge in graph.edges.values():
        print(f"  {edge.from_node} → {edge.to_node}: cost={edge.cost:.0f}")
    print()


def main() -> None:
    print("=" * 70)
    print("Network Transport Solver - WebAgg Backend")
    print("=" * 70)
    print()
    print("Matplotlib will open in your BROWSER automatically!")
    print("Default URL: http://localhost:8988")
    print()
    print("=" * 70)
    print()
    
    graph = create_railway_network()
    
    run_interactive_demo(
        graph,
        title="Railway Cargo Transportation Problem (Web)",
        info_printer=print_network_info
    )


if __name__ == "__main__":
    main()
