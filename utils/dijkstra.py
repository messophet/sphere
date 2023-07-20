from typing import Tuple, List
from typing import Dict
import numpy as np
import networkx as nx


def find_path_with_traffic(G: nx.MultiDiGraph,
                           source: str,
                           target: str,
                           traffic_data: Dict[str, int] = None) -> Tuple[float, List[str]]:
    """
    This function will find the shortest path between source and target in the graph G.
    :param G:
    :param source:
    :param target:
    :param traffic_data:
    :return:

    Each edge in the OSMnx graph represents a street segment and has a unique ID.
    Example of traffic data:
        traffic_data = {
            ("316226685", "53015629", 0): 5,  # Add 5 units of time to the edge from node 316226685 to node 53015629
            ("53015629", "316226685", 0): 10,  # Add 10 units of time to the edge from node 53015629 to node 316226685
            # More traffic data...
        }
    """
    # Define a new graph to perform Dijkstra's algorithm on
    G_dijkstra = G.copy()

    # Add traffic data into the edge weights
    if traffic_data is not None:
        for u, v, key, data in G_dijkstra.edges(keys=True, data=True):
            edge_id = f"{u}-{v}-{key}"
            if edge_id in traffic_data:
                data["time"] += traffic_data[edge_id]

    # Perform Dijkstra's algorithm
    try:
        cost, path = nx.single_source_dijkstra(G_dijkstra, source, target, weight='time')
    except nx.NetworkXNoPath:
        print(f"No path could be found between {source} and {target}")
        cost = np.inf
        path = []
    except nx.NodeNotFound as e:
        print(f"Node not found: {e}")
        cost = np.inf
        path = []

    return cost, path
