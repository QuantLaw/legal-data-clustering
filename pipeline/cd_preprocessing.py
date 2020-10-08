import itertools
import os
import re
from collections import Counter

import networkx as nx
import pandas as pd

from clustering_utils.graph_api import quotient_decision_graph
from clustering_utils.nodes_merging import quotient_graph_with_merge
from clustering_utils.utils import filename_for_pp_config
from quantlaw.utils.files import ensure_exists, list_dir
from quantlaw.utils.networkx import decay_function, sequence_graph

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
        v: k for k, v in nx.get_node_attributes(G, "citekey").items() if v
    }
    for k, v in nodes_mapping.items():
        if "citekey" in G_orig.nodes[k]:
            citekey = G_orig.nodes[k]["citekey"]
            simplified_citekey = simplify_citekey(citekey)
            if (
                simplified_citekey in nodes_citekey_mapping
                and nodes_citekey_mapping[simplified_citekey] != v
            ):
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
            edges = [
                (u, v, d["weight"])
                for u, v, d in C_merged.edges(node, data=True)
                if d["edge_type"] == "reference"
            ]

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
        print(
            "cooccurrence_factor",
            cooccurrence_factor,
            "for",
            filename_for_pp_config(**config, file_ext=""),
        )

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

    return missing_nodes
