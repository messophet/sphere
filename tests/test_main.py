
from models.TrafficPoint import TrafficPoint
from models.User import User
from utils.paths import set_path_for_user, apply_traffic_data, update_traffic_for_user
import unittest
from unittest.mock import patch
import networkx as nx
import pickle
import fakeredis


class TestPaths(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.redis = fakeredis.FakeStrictRedis()
        # Set up a simple graph for testing
        G = nx.MultiDiGraph()

        G.add_node(1, x=1.0, y=1.0, osmid=1)
        G.add_node(2, x=2.0, y=2.0, osmid=2)
        G.add_node(3, x=3.0, y=3.0, osmid=3)
        G.add_edge(1, 2, key=0, weight=1.0, osmid=0)
        G.add_edge(2, 3, key=0, weight=1.0, osmid=0)

        G.graph["crs"] = "EPSG:4326"

        self.G = G
        self.redis.set("graph_testuser", pickle.dumps(G))

    def test_apply_traffic_data(self):
        # Create a simple graph
        G = nx.DiGraph()

        # Manually add nodes and edges
        G.add_node(1, y=51.5074, x=-0.1278)  # London
        G.add_node(2, y=48.8566, x=2.3522)  # Paris
        G.add_node(3, y=41.9028, x=12.4964)  # Rome

        G.add_edge(1, 2, weight=1)
        G.add_edge(2, 3, weight=1)

        # Create traffic data
        traffic_data = [
            TrafficPoint(latitude=51.5074, longitude=-0.1278, delay=10),  # London
            TrafficPoint(latitude=48.8566, longitude=2.3522, delay=20),  # Paris
            TrafficPoint(latitude=41.9028, longitude=12.4964, delay=30),  # Rome
        ]

        def mock_nearest_nodes(*args, **kwargs):
            # first run, mock edge between [1, 2]
            # second run, mock edge between [2, 3]
            yield [1]
            yield [2]
            yield [2]
            yield [3]

        mock_nearest_nodes_gen = mock_nearest_nodes()

        # Mock osmnx.distance.nearest_nodes
        with patch('utils.paths.ox.nearest_nodes', side_effect=mock_nearest_nodes_gen):
            apply_traffic_data(G, traffic_data)

        # Check if the delays were correctly added to the edges
        self.assertEqual(G[1][2]['weight'], 21)  # From 1 to 20 (delay added to initial weight)
        self.assertEqual(G[2][3]['weight'], 31)  # From 1 to 30 (delay added to initial weight)

    async def test_set_path_for_user(self):
        with patch('osmnx.graph_from_bbox', return_value=self.G), \
             patch('osmnx.distance.nearest_nodes', side_effect=lambda G, X, Y: [1, 2]), \
             patch('utils.dijkstra.find_path_with_traffic', return_value=(1, [1, 2])), \
             patch('main.redis.Redis', return_value=self.redis):
            user = User(
                userid="testuser",
                longitude=1.0,
                latitude=1.0,
                end_longitude=2.0,
                end_latitude=2.0,
                traffic_data=[]
            )
            response = await set_path_for_user(user, self.redis)
            # Check that the response is as expected
            expected_path = {"path": [(1.0, 1.0), (2.0, 2.0)]}
            self.assertEqual(response, expected_path)

    async def test_update_traffic_for_user(self):
        traffic_point = TrafficPoint(latitude=1.0, longitude=1.0, delay=10)

        user = User(
            userid="testuser",
            longitude=1.0,
            latitude=1.0,
            end_longitude=2.0,
            end_latitude=2.0,
            traffic_data=[traffic_point]
        )

        with patch('main.redis.Redis', return_value=self.redis):
            response = await update_traffic_for_user(user, self.redis)

            # Check that the response is as expected
            expected_path = {"path": [(1.0, 1.0), (2.0, 2.0)]}
            self.assertEqual(response, expected_path)

            # Check that the graph was updated in Redis
            new_G = pickle.loads(self.redis.get(f"graph_{user.userid}"))
            self.assertEqual(new_G.edges[1, 2, 0]['weight'], self.G.edges[1, 2, 0]['weight'])


if __name__ == '__main__':
    unittest.main()
