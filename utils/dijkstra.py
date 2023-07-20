from typing import List
from models.TrafficPoint import TrafficPoint
import numpy as np
import networkx as nx


async def find_path_with_traffic(G: nx.MultiDiGraph,
                                 source: str,
                                 target: str,
                                 traffic_data: List[TrafficPoint]):
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
            latitude=51.5074, longitude=-0.1278, delay=10,  # Add 10 units of time (minutes) to the edge
                                                              derived from the latitude and longitude
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
