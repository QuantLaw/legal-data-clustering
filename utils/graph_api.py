import itertools
from collections import Counter

import networkx as nx
from cdlib import NodeClustering

from legal_data_preprocessing.utils.graph_api import *


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


def get_clustering_result(cluster_path, dataset, graph_type):
    """
    read the clustering result and the respective graph.
    ::param cluster_path: path of the cdlib.readwrite.write_community_json output
    ::param dataset: 'de' or 'us'
    ::param graph_type: 'clustering' for the rolled up graph. Other options: subseqitems, seqitems
    """

    # TODO LATER use statics for paths

    filename_base = os.path.splitext(os.path.split(cluster_path)[-1])[0]
    snapshot = filename_base.split("_")[0]
    dataset_folder = f"{dataset.upper()}-data"

    if graph_type == "clustering":
        graph_filename = "_".join(filename_base.split("_")[:4])
        graph_path = (
            f"../{dataset_folder}/cd_1_preprocessed_graph/{graph_filename}.gpickle.gz"
        )
        G = nx.read_gpickle(graph_path)
    elif graph_type in ["seqitems", "subseqitems"]:
        if dataset == "de":
            graph_folder = "11_crossreference_graph"
        elif dataset == "us":
            graph_folder = "7_crossreference_graph"
        else:
            raise Exception(f"dataset {dataset} is not an allowed")
        graph_path = (
            f"../{dataset_folder}/{graph_folder}/{graph_type}/{snapshot}.gpickle.gz"
        )
        G = nx.read_gpickle(graph_path)

    else:
        raise Exception(f"graph_type {graph_type} not allowed")

    clustering = readwrite.read_community_json(cluster_path)
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


def get_leaves(G):
    H = hierarchy_graph(G)
    return set([node for node in H.nodes if H.out_degree(node) == 0])


def get_leaves_with_communities(G):
    return {
        node: G.nodes[node]["communities"]
        for node in get_leaves(G)
        if "communities"
        in G.nodes[node]  # TODO LATER subseqitems do not have a parent seqitem
    }


def get_community_ids(clustering: NodeClustering):
    return sorted(
        set(itertools.chain.from_iterable(clustering.to_node_community_map().values()))
    )
