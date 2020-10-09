import itertools
import os
from collections import Counter, defaultdict

import networkx as nx

from cdlib import NodeClustering, readwrite
from legal_data_clustering.clustering_utils.utils import (
    filename_for_pp_config, get_config_from_filename,
    simplify_config_for_preprocessed_graph)
from quantlaw.utils.networkx import get_leaves, hierarchy_graph
from statics import (DE_CD_CLUSTER_PATH, DE_CD_PREPROCESSED_GRAPH_PATH,
                     DE_CROSSREFERENCE_GRAPH_PATH, US_CD_CLUSTER_PATH,
                     US_CD_PREPROCESSED_GRAPH_PATH,
                     US_CROSSREFERENCE_GRAPH_PATH)


def add_communities_to_graph(clustering: NodeClustering):
    """
    Assign community labels to nodes of the graph, propagating community labels from higher levels down the tree.
    """
    community_attrs = {}
    cluster_object_attrs = {}
    hG = hierarchy_graph(clustering.graph)
    for node_key, community_ids in clustering.to_node_community_map().items():
        node_with_descendants = [node_key] + [n for n in nx.descendants(hG, node_key)]
        for node in node_with_descendants:
            community_attrs[node] = community_ids
        cluster_object_attrs[node] = True

    nx.set_node_attributes(clustering.graph, community_attrs, "communities")
    nx.set_node_attributes(clustering.graph, cluster_object_attrs, "clusterobject")


def add_community_to_graph(clustering: NodeClustering):
    communities = nx.get_node_attributes(clustering.graph, "communities")
    if not len(communities):
        raise Exception(
            "No communities found in graph. "
            'Call "add_communities_to_graph" before calling "add_community_to_graph"'
        )
    for node, community_attr in communities.items():
        if len(community_attr) > 1:
            raise Exception(
                f"Node {node} has too many communities assigned: {community_attr}"
            )

    community = {k: v[0] for k, v in communities.items()}
    nx.set_node_attributes(clustering.graph, community, "community")


def get_clustering_result(cluster_path, dataset, graph_type, path_prefix=""):
    """
    read the clustering result and the respective graph.
    ::param cluster_path: path of the cdlib.readwrite.write_community_json output
    ::param dataset: 'de' or 'us'
    ::param graph_type: 'clustering' for the rolled up graph. Other options: subseqitems, seqitems
    """

    filename_base = os.path.splitext(os.path.split(cluster_path)[-1])[0]
    snapshot = filename_base.split("_")[0]

    if graph_type == "clustering":
        config = get_config_from_filename(filename_base)
        graph_filename = filename_for_pp_config(
            **simplify_config_for_preprocessed_graph(config)
        )
        graph_path = path_prefix + (
            US_CD_PREPROCESSED_GRAPH_PATH
            if dataset.lower() == "us"
            else DE_CD_PREPROCESSED_GRAPH_PATH
        )
        graph_path += f"/{graph_filename}"
        G = nx.read_gpickle(graph_path)
    elif graph_type in ["seqitems", "subseqitems"]:
        graph_path = path_prefix + (
            US_CROSSREFERENCE_GRAPH_PATH
            if dataset.lower() == "us"
            else DE_CROSSREFERENCE_GRAPH_PATH
        )

        graph_path += f"/{graph_type}/{snapshot}.gpickle.gz"
        G = nx.read_gpickle(graph_path)

    else:
        raise Exception(f"graph_type {graph_type} not allowed")

    clustering = readwrite.read_community_json(
        path_prefix
        + (US_CD_CLUSTER_PATH if dataset.lower() == "us" else DE_CD_CLUSTER_PATH)
        + "/"
        + os.path.split(cluster_path)[-1]
    )
    clustering.graph = G

    add_communities_to_graph(clustering)

    return clustering


def get_community_law_name_counters(clustering: NodeClustering, count_level: str):
    """
    Counting the law_names in each cluster.
    :param clustering:
    :param count_level:
    The level at which nodes will be counted.
    The clustering must have at least the granularity of the count_level.
    Eg graph_type=clustering and count_level=seqitem is not allowed.
    :return: dict with community ids and  counters
    """

    if count_level == "seqitems":
        node_type = "seqitem"
    elif count_level == "subseqitems":
        node_type = "subseqitem"
    elif count_level == "clustering":
        raise Exception(f"Not yet implemented")
    else:
        raise Exception(f"Wrong argument {count_level}")

    leaves_data_at_level = [
        data
        for n, data in clustering.graph.nodes(data=True)
        # exclude root and filter afterwards
        if data["level"] != -1 and data["type"] == node_type
    ]
    counters = dict()
    for community_id in range(len(clustering.communities)):
        counters[community_id] = Counter(
            [
                "_".join(data["key"].split("_")[:-1])
                for data in leaves_data_at_level
                if data.get("community") == community_id
            ]
        )
    return counters


def get_leaves_with_communities(G):
    return {
        node: G.nodes[node]["communities"]
        for node in get_leaves(G)
        if "communities" in G.nodes[node]
    }


def get_community_ids(clustering: NodeClustering):
    return sorted(
        set(itertools.chain.from_iterable(clustering.to_node_community_map().values()))
    )


def quotient_decision_graph(G, merge_decisions, merge_statutes):
    H = nx.DiGraph()

    # Decision nodes and containment edges
    if merge_decisions:
        documents = [n for n, b in G.nodes(data="type") if b == "document"]
        H.add_nodes_from([(n.split("_")[0], G.nodes[n]) for n in documents])
    else:
        decisions = [n for n, b in G.nodes(data="bipartite") if b == "decision"]
        H.add_nodes_from([(n, G.nodes[n]) for n in decisions])

        containment = [
            (u, v, d)
            for u, v, d in G.edges(data=True)
            if d["edge_type"] == "containment"
        ]
        H.add_edges_from(containment)

    # Statute nodes
    if merge_statutes:
        statute_nodes = [n for n, b in G.nodes(data="bipartite") if b == "statute"]
        statute_nodes_merged = list(sorted({n.split("_")[0] for n in statute_nodes}))
        H.add_nodes_from(statute_nodes_merged, bipartite="statute")
    else:
        statute_nodes = [n for n, b in G.nodes(data="bipartite") if b == "statute"]
        H.add_nodes_from([(n, G.nodes[n]) for n in statute_nodes])

    # Reference edges
    references = [
        [u, v, d] for u, v, d in G.edges(data=True) if d["edge_type"] == "reference"
    ]

    references_dict = defaultdict(int)
    for u, v, d in references:
        u_converted = u.split("_")[0] if merge_decisions else u
        v_converted = v.split("_")[0] if merge_statutes else v
        references_dict[(u_converted, v_converted)] += d["weight"]

    references_converted = [
        (k[0], k[1], {"weight": v, "edge_type": "reference"})
        for k, v in references_dict.items()
    ]
    H.add_edges_from(references_converted)

    return H


def cluster_families(G, threshold):
    H = filter_edges_for_cluster_families(G, threshold, "tokens_n")
    components = list(nx.connected_components(H.to_undirected()))
    components.sort(
        key=lambda nodes_set: (
            max([H.nodes[n]["tokens_n"] for n in nodes_set]),
            sorted(nodes_set)[-1],
        ),
        reverse=True,
    )
    components = [
        sorted(c, key=lambda n: (H.nodes[n]["tokens_n"], n), reverse=True)
        for c in components
    ]
    return components


def filter_edges_for_cluster_families(G, threshold, attr):
    edges_to_remove = [
        (u, v)
        for u, v, data in G.edges(data=True)
        if (
            data[attr] < G.nodes[u][attr] * threshold
            or data[attr] < G.nodes[v][attr] * threshold
        )
    ]
    H = G.copy()
    H.remove_edges_from(edges_to_remove)
    return H


def get_heading_path(G_hierarchy: nx.DiGraph, n):
    if n == "root":
        return ""
    predecessors = list(G_hierarchy.predecessors(n))
    assert len(predecessors) <= 1
    heading = G_hierarchy.nodes[n].get("heading", "-")
    if predecessors and predecessors != ["root"]:
        predecessor = predecessors[0]
        heading = get_heading_path(G_hierarchy, predecessor) + " / " + heading
    return heading


def add_headings_path(G):
    H = hierarchy_graph(G)
    heading_paths = {}
    for key in H.nodes:
        heading_paths[key] = "/".join(get_heading_path(H, key))
    nx.set_node_attributes(G, heading_paths, "heading_path")
