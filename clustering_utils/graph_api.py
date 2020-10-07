import itertools
import os
from collections import Counter, defaultdict

import networkx as nx
from cdlib import NodeClustering, readwrite
from quantlaw.utils.networkx import hierarchy_graph

from statics import (
    US_CROSSREFERENCE_GRAPH_PATH,
    DE_CROSSREFERENCE_GRAPH_PATH,
    US_CD_CLUSTER_PATH,
    DE_CD_CLUSTER_PATH,
    US_CD_PREPROCESSED_GRAPH_PATH,
    DE_CD_PREPROCESSED_GRAPH_PATH,
)
from clustering_utils.utils import (
    get_config_from_filename,
    filename_for_pp_config,
    simplify_config_for_preprocessed_graph,
)


def decay_function(key):
    """
    Returns a decay function to create a weighted sequence graph.
    """
    return lambda x: (x - 1) ** (-key)


def sequence_graph(G, seq_decay_func=decay_function(1), seq_ref_ratio=1):
    """
    Creates sequence graph for G, consisting of seqitems and their cross-references only,
    where neighboring seqitems are connected via edges in both directions.
    :param seq_decay_func: function to calculate sequence edge weight based on distance between neighboring nodes
    :param seq_ref_ratio: ratio between a sequence edge weight when nodes in the sequence are at minimum distance
           from each other and a reference edge weight
    """

    hG = hierarchy_graph(G)
    # make sure we get _all_ seqitems as leaves, not only the ones without outgoing references
    leaves = [n for n in hG.nodes() if hG.out_degree(n) == 0]

    sG = nx.MultiDiGraph(nx.induced_subgraph(G, leaves))

    if seq_ref_ratio:
        nx.set_edge_attributes(sG, 1 / seq_ref_ratio, name="weight")
        node_headings = dict(sG.nodes(data="heading"))
        ordered_seqitems = sorted(list(node_headings.keys()))

        # connect neighboring seqitems sequentially
        new_edges = get_new_edges(G, ordered_seqitems, seq_decay_func)
        sG.add_edges_from(new_edges)
    else:
        nx.set_edge_attributes(sG, 1, name="weight")

    sG.graph["name"] = f'{G.graph["name"]}_sequence_graph_seq_ref_ratio_{seq_ref_ratio}'

    return sG


def get_new_edges(G, ordered_seqitems, seq_decay_func):
    """
    Convenience function to avoid list comprehension over four lines.
    """
    there = []
    back = []
    hG = hierarchy_graph(G).to_undirected()
    for idx, n in enumerate(ordered_seqitems[:-1]):
        next_item = ordered_seqitems[idx + 1]
        if (
            n.split("_")[0] == next_item.split("_")[0]
        ):  # n and next_item are in the same law
            distance = nx.shortest_path_length(hG, source=n, target=next_item)
            weight = seq_decay_func(distance)
            there.append(
                (
                    n,
                    next_item,
                    {"edge_type": "sequence", "weight": weight, "backwards": False},
                )
            )
            back.append(
                (
                    next_item,
                    n,
                    {"edge_type": "sequence", "weight": weight, "backwards": True},
                )
            )
    return there + back


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
    dataset_folder = f"{dataset.upper()}-data"

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


def get_leaves(G):
    H = hierarchy_graph(G)
    return set([node for node in H.nodes if H.out_degree(node) == 0])


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


def quotient_graph(
    G,
    node_attribute,
    edge_types=["reference", "cooccurrence"],
    self_loops=False,
    root_level=-1,
    aggregation_attrs=("chars_n", "chars_nowhites", "tokens_n", "tokens_unique"),
):
    """
    Generate the quotient graph with all nodes sharing the same node_attribute condensed into a single node.
    Attribute aggregation functions not currently implemented; primary use case currently aggregation by law_name.
    """

    # node_key:attribute_value map
    attribute_data = dict(G.nodes(data=node_attribute))
    # set cluster -1 if they were not part of the clustering (guess: those are empty laws)
    attribute_data = {
        k: (v if v is not None else -1) for k, v in attribute_data.items()
    }
    # unique values in that map
    unique_values = sorted(list(set(attribute_data.values())))

    # remove the root if root_level is given
    if root_level is not None:
        roots = [x for x in G.nodes() if G.nodes[x]["level"] == root_level]
        if roots:
            root = roots[0]
            unique_values.remove(root)
        else:
            root = None
    else:
        root = None

    # build a new MultiDiGraph
    nG = nx.MultiDiGraph()

    # add nodes
    new_nodes = {x: [] for x in unique_values}
    nG.add_nodes_from(unique_values)

    # sort nodes into buckets
    for n in attribute_data.keys():
        if n != root:
            mapped_to = attribute_data[n]
            new_nodes[mapped_to].append(n)
            if G.nodes[n].get("heading") == mapped_to:
                for x in G.nodes[n].keys():
                    nG.nodes[mapped_to][x] = G.nodes[n][x]

    # add edges
    for e in G.edges(data=True):
        if e[-1]["edge_type"] not in edge_types:
            continue
        if (True if self_loops else attribute_data[e[0]] != attribute_data[e[1]]) and (
            True if root_level is None else G.nodes[e[0]]["level"] != root_level
        ):  # special treatment for root
            k = nG.add_edge(
                attribute_data[e[0]], attribute_data[e[1]], edge_type=e[-1]["edge_type"]
            )
            if e[-1]["edge_type"] == "sequence":
                nG.edges[attribute_data[e[0]], attribute_data[e[1]], k]["weight"] = e[
                    -1
                ]["weight"]

    nG.graph["name"] = f'{G.graph["name"]}_quotient_graph_{node_attribute}'

    if aggregation_attrs:
        aggregate_attr_in_quotient_graph(nG, G, new_nodes, aggregation_attrs)

    return nG


def aggregate_attr_in_quotient_graph(nG, G, new_nodes, aggregation_attrs):
    """
    Sums attributes of nodes in an original graph per community and adds the sum to the nodes in a quotient graph.
    :param nG: Quotient graph
    :param G: Original graph
    :param new_nodes: Mapping of nodes in the quotient graph to an iterable of nodes in the original graph
        that are represented by the node in the quotient graph.
    :param aggregation_attrs: attributes to aggregate
    """
    for attr in aggregation_attrs:
        attr_data = nx.get_node_attributes(G, attr)
        for community_id, nodes in new_nodes.items():
            aggregated_value = sum(attr_data.get(n) for n in nodes)
            nG.nodes[community_id][attr] = aggregated_value


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
