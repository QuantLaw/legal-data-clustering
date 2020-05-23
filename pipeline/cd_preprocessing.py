import itertools
import os
import re
from collections import Counter

import networkx as nx
import regex
import pandas as pd

from legal_data_preprocessing.utils.common import ensure_exists, list_dir
from legal_data_preprocessing.utils.graph_api import (
    hierarchy_graph,
    sequence_graph,
    decay_function,
)
from utils.graph_api import quotient_decision_graph
from utils.utils import filename_for_pp_config

target_file_ext = ".gpickle.gz"


def cd_preprocessing_prepare(
    overwrite, snapshots, pp_configs, source_folder, target_folder
):
    ensure_exists(target_folder)
    items = [
        dict(
            snapshot=snapshot,
            pp_ratio=pp_ratio,
            pp_decay=pp_decay,
            pp_merge=pp_merge,
            pp_co_occurrence=pp_co_occurrence,
            pp_co_occurrence_type=pp_co_occurrence_type,
        )
        for snapshot in snapshots
        for pp_ratio in pp_configs["pp_ratios"]
        for pp_decay in pp_configs["pp_decays"]
        for pp_merge in pp_configs["pp_merges"]
        for pp_co_occurrence in pp_configs["pp_co_occurrences"]
        for pp_co_occurrence_type in pp_configs["pp_co_occurrence_types"]
    ]

    # Check if source graphs exist
    existing_source_files = set(list_dir(f"{source_folder}/seqitems", ".gpickle.gz"))
    required_source_files = {f"{snapshot}.gpickle.gz" for snapshot in snapshots}
    missing_source_files = required_source_files - existing_source_files
    if len(missing_source_files):
        raise Exception(
            f'Source graphs are missing: {" ".join(sorted(missing_source_files))}'
        )

    if not overwrite:
        existing_files = list_dir(target_folder, target_file_ext)
        items = [
            item
            for item in items
            if filename_for_pp_config(**item, file_ext=target_file_ext)
            not in existing_files
        ]

    return items


def get_decision_network(path):
    """Get decision network. Load or get from cache"""
    if not getattr(get_decision_network, "_cache", None):
        get_decision_network._cache = {}
    if path not in get_decision_network._cache:
        get_decision_network._cache[path] = nx.read_gpickle(path)
    return get_decision_network._cache[path]


def cd_preprocessing(config, source_folder, target_folder, decision_network_path):
    source_path = f"{source_folder}/seqitems/{config['snapshot']}.gpickle.gz"
    graph_target_path = (
        f"{target_folder}/{filename_for_pp_config(**config, file_ext=target_file_ext)}"
    )
    missing_nodes_target_path = os.path.join(
        target_folder,
        filename_for_pp_config(**config, file_ext="_missing_co_occurr_nodes.csv"),
    )

    seq_decay_func = decay_function(config["pp_decay"])

    G = nx.read_gpickle(source_path)
    mqG, nodes_mapping = quotient_graph_with_merge(
        G, merge_threshold=config["pp_merge"]
    )

    smqG = sequence_graph(
        mqG, seq_decay_func=seq_decay_func, seq_ref_ratio=config["pp_ratio"]
    )

    if config["pp_co_occurrence"] != 0:
        missing_nodes = add_co_occurrences(
            config, smqG, G, nodes_mapping, decision_network_path
        )

        pd.DataFrame(
            list(missing_nodes.items()), columns=["missing_node", "count"]
        ).sort_values("count", ascending=False).to_csv(
            missing_nodes_target_path, index=False
        )

    if config["pp_co_occurrence"] == -1:
        edges_to_remove = [
            (u, v, k)
            for u, v, k, t in smqG.edges(keys=True, data="edge_type")
            if t == "reference"
        ]
        smqG.remove_edges_from(edges_to_remove)

    nx.write_gpickle(smqG, graph_target_path)


###################
# Merge graph nodes
###################


def quotient_graph_with_merge(
    G, self_loops=False, merge_threshold=0, merge_attribute="chars_n"
):
    """
    Generate the quotient graph, recursively merging nodes if the merge result does not exceed merge threshold.
    or merge threshold 0 this rolls up all node whose siblings are exclusively nodes with merge attribute value 0.
    """

    hG = hierarchy_graph(G)

    # build a new MultiDiGraph
    nG = nx.MultiDiGraph()

    # create a mapping especially for contracted nodes to draw edges between the remaining nodes appropriately
    nodes_mapping = {}

    for node_id, node_attrs in G.nodes(data=True):
        # Skip root node
        # if hG.in_degree(node_id) == 0:
        #     continue

        if is_node_contracted(hG, node_id, merge_threshold, merge_attribute):
            # Add node to mapping to draw edges appropriately between contracted nodes
            # print(f"-", end="")

            merge_parent = get_merge_parent(
                hG, node_id, merge_threshold, merge_attribute
            )
            nodes_mapping[node_id] = merge_parent
        else:
            # print(f"+", end="")
            # Add node to ne graph and add node to mapping for convenience
            nG.add_node(node_id, **node_attrs)
            nodes_mapping[node_id] = node_id

        # parent = (
        #     list(hG.predecessors(node_id))[0]
        #     if list(hG.predecessors(node_id))
        #     else None
        # )
        # print(
        #     f" {node_id} < {parent} -- {hG.nodes[parent].get(merge_attribute) if parent else None}"
        # )

    for e_source, e_target, e_data in G.edges(data=True):
        if e_data["edge_type"] in {"reference", "identity"}:
            # get source and target of edge in quotient graph
            source = nodes_mapping[e_source]
            target = nodes_mapping[e_target]
            if self_loops or source != target:  # skip self loops, if deactivated
                nG.add_edge(source, target, **e_data)
        else:
            # add containment edge if target is still in quotient graph
            if e_target in nG:
                nG.add_edge(e_source, e_target, **e_data)

    nG.graph[
        "name"
    ] = f'{G.graph["name"]}_merged_quotient_graph_{merge_attribute}_{merge_threshold}'

    return nG, nodes_mapping


def get_merge_parent(G, node, merge_threshold=0, merge_attribute="chars_n"):
    """
    Gets the first predecessor that is not contracted
    """
    if not is_node_contracted(G, node, merge_threshold, merge_attribute):
        return node

    parent = list(G.predecessors(node))[0]
    return get_merge_parent(G, parent, merge_threshold, merge_attribute)


chapter_buch_pattern = regex.compile(r"\w*\s*\bBuch\b|CHAPTER")


def is_node_contracted(G, node, merge_threshold=0, merge_attribute="chars_n"):
    """
    Determines whether a node should be in the quotient graph
    :param G: hierarchical graph
    :param node: current node name
    :param merge_threshold:
    :param merge_attribute:
    :return: boolean
    """
    # Is a root node?
    if G.in_degree(node) == 0:
        # print(" root ", end="")
        return False

    parent = list(G.predecessors(node))[0]

    # Is child of a root node ?
    if G.in_degree(parent) == 0:
        # print(" root2 ", end="")
        return False

    if merge_threshold == -1:
        # DEBUG
        # ancestors = [
        #     (
        #         ancestor,
        #         G.nodes[ancestor]['heading'],
        #         chapter_buch_pattern.match(G.nodes[ancestor]['heading']),
        #         G.nodes[ancestor]['level']
        #     )
        #     for ancestor in nx.ancestors(G, node)
        #     if ancestor != 'root'
        # ]

        # Is book or chapter
        if "heading" in G.nodes[node] and chapter_buch_pattern.match(
            G.nodes[node]["heading"]
        ):
            return False

        if [
            ancestor
            for ancestor in nx.ancestors(G, node)
            if ancestor != "root"
            and "heading" in G.nodes[ancestor]
            and chapter_buch_pattern.match(G.nodes[ancestor]["heading"])
        ]:
            # Book or chapter above
            return True

        if [
            predecessor
            for predecessor in nx.predecessor(G, node)
            if predecessor != "root"
            and "heading" in G.nodes[predecessor]
            and chapter_buch_pattern.match(G.nodes[predecessor]["heading"])
        ]:
            # Book or chapter below
            return False
        else:
            # No chapter or book in branch
            return True

    else:

        # Is parent too "big" to be a leaf? In this implementation node and their siblings are connected is the parent,
        # they are contracted in, is still below a certain threshold. It is also possible to contract all a node and its
        # siblings if one node is below a certain threshold but the parent would be above the threshold.
        if G.nodes[parent][merge_attribute] > merge_threshold:
            # print(
            #     f"merge_threshold of {node} < {parent} -- {G.nodes[parent][merge_attribute]}"
            # )
            return False

        return True


simplify_citekey_pattern = re.compile(r"(.+)[\-\–]\d{4}")


def simplify_citekey(citekey):
    citekey_law, citekey_nr = citekey.split("_")
    match = simplify_citekey_pattern.fullmatch(citekey_law)
    if match:
        return match[1] + "_" + citekey_nr
    else:
        return citekey


def add_co_occurrences(config, G, G_orig, nodes_mapping, decision_network_path):
    C = get_decision_network(decision_network_path)
    cooccurrence_weight = (
        config["pp_co_occurrence"] if config["pp_co_occurrence"] > 0 else 1
    )

    if config["pp_co_occurrence_type"] == "decision":
        merge_decisions = True
    elif config["pp_co_occurrence_type"] == "paragraph":
        merge_decisions = False
    else:
        raise Exception(f"{config['pp_co_occurrence_type']} is not a valid option")

    C_merged = quotient_decision_graph(
        C, merge_decisions=merge_decisions, merge_statutes=False
    )

    nodes_citekey_mapping = {
        k: v for k, v in nx.get_node_attributes(G, "citekey").items() if v
    }
    for k, v in nodes_mapping.items():
        if "citekey" in G_orig.nodes[k]:
            citekey = G_orig.nodes[k]["citekey"]
            simplified_citekey = simplify_citekey(citekey)
            if simplified_citekey in nodes_citekey_mapping:
                print(
                    "Conflict:",
                    simplified_citekey,
                    nodes_citekey_mapping[simplified_citekey],
                    v,
                )
            nodes_citekey_mapping[simplified_citekey] = v

    missing_nodes = Counter()

    co_occurrence_edges = Counter()
    for node in C_merged.nodes:
        if C_merged.nodes[node]["bipartite"] == "decision":
            edges = list(C_merged.edges(node, data="weight"))

            simplified_citekeys = [simplify_citekey(v) for u, v, w in edges]

            targets = {
                nodes_citekey_mapping[v]
                for v in simplified_citekeys
                if v in nodes_citekey_mapping
            }
            targets_missing = {
                v for v in simplified_citekeys if v not in nodes_citekey_mapping
            }
            missing_nodes.update(targets_missing)

            targets_combinations = list(itertools.combinations(targets, 2))
            for target_a, target_b in targets_combinations:
                co_occurrence_edges[(target_a, target_b)] += 1

    G.add_edges_from(
        [
            (u, v, dict(weight=cnt * cooccurrence_weight, edge_type="cooccurrence"))
            for (u, v), cnt in co_occurrence_edges.items()
        ]
    )
    G.add_edges_from(
        [
            (
                v,
                u,
                dict(
                    weight=cnt * cooccurrence_weight,
                    edge_type="cooccurrence",
                    reverse=True,
                ),
            )
            for (u, v), cnt in co_occurrence_edges.items()
        ]
    )

    if config["pp_co_occurrence"] == -2:
        # Set weight of co-occurrence-edges that sum of weights equals the sum of weights of cross-references
        total_weight_cooccurrence = sum(
            G.edges[u, v, k]["weight"]
            for u, v, k, edge_type in G.edges(keys=True, data="edge_type")
            if edge_type == "cooccurrence"
        )
        total_weight_reference = sum(
            G.edges[u, v, k]["weight"]
            for u, v, k, edge_type in G.edges(keys=True, data="edge_type")
            if edge_type == "reference"
        )

        cooccurrence_factor = total_weight_reference / total_weight_cooccurrence
        print(total_weight_reference, total_weight_cooccurrence, cooccurrence_factor)

        for u, v, k, edge_type in G.edges(keys=True, data="edge_type"):
            if edge_type == "cooccurrence":
                G.edges[u, v, k]["weight"] *= cooccurrence_factor

        total_weight_cooccurrence = sum(
            G.edges[u, v, k]["weight"]
            for u, v, k, edge_type in G.edges(keys=True, data="edge_type")
            if edge_type == "cooccurrence"
        )
        total_weight_reference = sum(
            G.edges[u, v, k]["weight"]
            for u, v, k, edge_type in G.edges(keys=True, data="edge_type")
            if edge_type == "reference"
        )
        print(total_weight_reference, total_weight_cooccurrence, cooccurrence_factor)

    return missing_nodes
