from typing import Optional, Callable
from .models.graph import Graph
from .ui import InteractiveSession, LayoutContext


def run_interactive_demo(
    graph: Graph,
    title: str,
    info_printer: Optional[Callable[[Graph], None]] = None
) -> None:
    """
    Run an interactive transport problem solver demonstration.

    Args:
        graph: The configured network graph to solve
        title: Title to display in console header
        info_printer: Optional function to print additional graph information
    
    Example:
        >>> graph = create_my_network()
        >>> run_interactive_demo(
        ...     graph,
        ...     "My Transport Problem",
        ...     info_printer=print_network_info
        ... )
    """
    print("=" * 70)
    print(title)
    print("=" * 70)
    print()
    
    print(f"Graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    total_supply = sum(n.balance for n in graph.nodes.values() if n.balance > 0)
    total_demand = -sum(n.balance for n in graph.nodes.values() if n.balance < 0)
    print(f"Total supply: {total_supply:.0f}")
    print(f"Total demand: {total_demand:.0f}")
    print()
    
    if info_printer:
        info_printer(graph)
    
    layout = LayoutContext()
    
    session = InteractiveSession(graph, layout)
    
    session.setup_and_run()
