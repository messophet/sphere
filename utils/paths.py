from typing import List
from utils.dijkstra import find_path_with_traffic
from models.User import User
from models.TrafficPoint import TrafficPoint
from utils.logger import logger
from utils.connection_manager import manager
import pickle
import redis
import osmnx as ox
import networkx as nx


async def set_path_for_user(user: User, r: redis.Redis):
    logger.info("Setting path for user %s", user.userid)

    # Get the user's current location and destination
    user_location = (user.latitude, user.longitude)
    user_destination = (user.end_latitude, user.end_longitude)

    # Compute the bounding box
    north, south = max(user_location[0], user_destination[0]), min(user_location[0], user_destination[0])
    east, west = max(user_location[1], user_destination[1]), min(user_location[1], user_destination[1])

    # Increase the bounding box size by a small factor to ensure start and end nodes are within graph
    margin = 0.01  # this is in degrees
    north += margin
    south -= margin
    east += margin
    west -= margin

    # Generate the OSMnx graph for the area between the user's location and their destination
    G = ox.graph_from_bbox(north, south, east, west, network_type="drive")

    # Get the closest nodes to the start and end points
    start_node = ox.nearest_nodes(G, X=[user.longitude], Y=[user.latitude])[0]
    end_node = ox.nearest_nodes(G, X=[user.end_longitude], Y=[user.end_latitude])[0]

    logger.info("Found start node %s and end node %s for user %s", start_node, end_node, user.userid)

    # Apply traffic data
    apply_traffic_data(G, user.traffic_data)

    # Find the shortest path
    cost, path = find_path_with_traffic(G, start_node, end_node, user.traffic_data)

    # Serialize the path and store it in Redis
    r.set(f"path_{user.userid}", pickle.dumps(path))

    # Convert path of node ids to longitude/latitude
    path_coordinates = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in path]  # (latitude, longitude)

    return {"path": path_coordinates}


async def update_traffic_for_user(user: User, r: redis.Redis):
    logger.info("Received traffic update for user %s", user.userid)

    # Check if the graph exists in Redis
    if not r.exists(f"graph_{user.userid}"):
        return {"error": "No path set for this user"}

    # Retrieve and deserialize the graph from Redis
    G = pickle.loads(r.get(f"graph_{user.userid}"))

    # Apply traffic data
    apply_traffic_data(G, user.traffic_data)

    # Serialize and store the updated graph back in Redis
    r.set(f"graph_{user.userid}", pickle.dumps(G))

    # Get the closest nodes to the start and end points
    start_node = ox.nearest_nodes(G, X=[user.longitude], Y=[user.latitude])[0]
    end_node = ox.nearest_nodes(G, X=[user.end_longitude], Y=[user.end_latitude])[0]

    # Find the new shortest path
    cost, path = find_path_with_traffic(G, start_node, end_node, user.traffic_data)

    # Convert path of node ids to longitude/latitude
    path_coordinates = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in path]  # (latitude, longitude)

    # Notify the user if they are connected via WebSocket
    if user.userid in manager.active_connections:
        await manager.send_personal_message(f"Updated path: {path_coordinates}", manager.active_connections[user.userid])

    return {"path": path_coordinates}


def apply_traffic_data(G: nx.DiGraph, traffic_data: List[TrafficPoint]):
    # For each pair of consecutive points, find the nearest nodes and create an edge with the delay as the weight
    for i in range(len(traffic_data) - 1):
        point1 = traffic_data[i]
        point2 = traffic_data[i + 1]

        # Find the nearest nodes for each point
        node1 = ox.nearest_nodes(G, X=[point1.longitude], Y=[point1.latitude])[0]
        node2 = ox.nearest_nodes(G, X=[point2.longitude], Y=[point2.latitude])[0]

        # Update the edge with the delay
        if G.has_edge(node1, node2):
            G[node1][node2]['weight'] += point2.delay
