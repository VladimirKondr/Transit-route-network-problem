from typing import Tuple
import math


def calculate_label_position(
    pos1: Tuple[float, float],
    pos2: Tuple[float, float],
    t: float = 0.5,
    offset: float = 0.15
) -> Tuple[float, float]:
    """
    Calculate label position along an edge with perpendicular offset.
    
    Args:
        pos1: Start position (x, y)
        pos2: End position (x, y)
        t: Parameter along edge (0.0 to 1.0)
        offset: Perpendicular offset from edge
    
    Returns:
        Label position (x, y)
    """
    x = pos1[0] + t * (pos2[0] - pos1[0])
    y = pos1[1] + t * (pos2[1] - pos1[1])
    
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    length = math.sqrt(dx**2 + dy**2)
    
    if length > 0:
        perp_x = -dy / length
        perp_y = dx / length
        
        x += perp_x * offset
        y += perp_y * offset
    
    return (x, y)


def project_point_to_edge(
    point: Tuple[float, float],
    pos1: Tuple[float, float],
    pos2: Tuple[float, float]
) -> Tuple[float, float]:
    """
    Project a point onto an edge and return parameter t and perpendicular offset.
    
    Args:
        point: Point to project (x, y)
        pos1: Edge start (x, y)
        pos2: Edge end (x, y)
    
    Returns:
        (t, offset) where t is parameter along edge, offset is perpendicular distance
    """
    px, py = point
    x1, y1 = pos1
    x2, y2 = pos2
    
    dx = x2 - x1
    dy = y2 - y1
    length_squared = dx**2 + dy**2
    
    if length_squared == 0:
        return (0.5, 0.0)
    
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / length_squared))
    
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    
    offset_x = px - closest_x
    offset_y = py - closest_y
    offset = math.sqrt(offset_x**2 + offset_y**2)
    
    cross = dx * offset_y - dy * offset_x
    if cross < 0:
        offset = -offset
    
    return (t, offset)
