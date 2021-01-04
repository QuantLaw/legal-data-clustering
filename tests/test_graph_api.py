import unittest
from copy import deepcopy

import networkx as nx
from cdlib import NodeClustering

from legal_data_clustering.utils.graph_api import (
    add_communities_to_graph,
    add_community_to_graph,
    filter_edges_for_cluster_families,
    get_heading_path,
    get_leaves_with_communities,
)


class TestGraphAPI(unittest.TestCase):
    def setUp(self):
        self.G_hierarchy = nx.DiGraph()
        self.G_hierarchy.add_node("root", **dict(attr=0))
        self.G_hierarchy.add_node(1, **dict(heading="Hello", attr=10))
        self.G_hierarchy.add_node(2, **dict(heading="World", attr=100))
        self.G_hierarchy.add_node(3, **dict(attr=1000, communities=[1, 2]))
        self.G_hierarchy.add_edges_from(
            [("root", 1), (1, 2), (1, 3)], **dict(attr=10, edge_type="containment")
        )
        self.G_hierarchy.graph["name"] = "G"
        self.clustering = NodeClustering([[1]], deepcopy(self.G_hierarchy), "dummy")
        self.clustering2 = NodeClustering([[1]], deepcopy(self.G_hierarchy), "dummy")

    def test_add_communities_to_graph(self):
        add_communities_to_graph(self.clustering)
        self.assertEqual(self.clustering.graph.nodes[1]["communities"], [0])
        self.assertEqual(self.clustering.graph.nodes[2]["communities"], [0])
        self.assertEqual(self.clustering.graph.nodes[3]["communities"], [0])

    def test_add_community_to_graph(self):
        with self.assertRaises(Exception):
            add_community_to_graph(self.clustering2)
        del self.clustering2.graph.nodes[3]["communities"]
        with self.assertRaises(Exception):
            add_community_to_graph(self.clustering2)
        add_communities_to_graph(self.clustering2)
        add_community_to_graph(self.clustering2)
        self.assertEqual(self.clustering2.graph.nodes[1]["community"], 0)

    def test_leaves_with_communities(self):
        self.assertEqual(get_leaves_with_communities(self.G_hierarchy), {3: [1, 2]})

    def test_filter_edges_for_cluster_families(self):
        H = filter_edges_for_cluster_families(self.G_hierarchy, 0.1, "attr")
        edges = list(H.edges)
        self.assertTrue((1, 3) not in edges)
        self.assertTrue((1, 2) in edges)
        self.assertTrue(("root", 1) in edges)

    def test_get_heading_path(self):
        self.assertEqual(get_heading_path(self.G_hierarchy, "root"), "")
        self.assertEqual(get_heading_path(self.G_hierarchy, 2), "Hello / World")
        self.assertEqual(get_heading_path(self.G_hierarchy, 3), "Hello / -")
