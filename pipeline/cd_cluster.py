import json
from collections import defaultdict
from itertools import combinations

import networkx as nx
import numpy as np
from cdlib import NodeClustering
from cdlib.readwrite import write_community_json

from pipeline import cdlib_custom_algorithms
from pipeline.cdlib_custom_algorithms import missings_nodes_as_additional_clusters
from legal_data_preprocessing.utils.common import ensure_exists, list_dir
from clustering_utils.utils import filename_for_pp_config

source_file_ext = ".gpickle.gz"
target_file_ext = ".json"


def cd_cluster_prepare(overwrite, snapshots, pp_configs, source_folder, target_folder):
    ensure_exists(target_folder)
    items = [
        dict(
            snapshot=snapshot,
            pp_ratio=pp_ratio,
            pp_decay=pp_decay,
            pp_merge=pp_merge,
            pp_co_occurrence=pp_co_occurrence,
            pp_co_occurrence_type=pp_co_occurrence_type,
            seed=seed,
            markov_time=markov_time,
            consensus=consensus,
            number_of_modules=number_of_modules,
            method=method,
        )
        for snapshot in snapshots
        for pp_ratio in pp_configs["pp_ratios"]
        for pp_decay in pp_configs["pp_decays"]
        for pp_merge in pp_configs["pp_merges"]
        for pp_co_occurrence in pp_configs["pp_co_occurrences"]
        for pp_co_occurrence_type in pp_configs["pp_co_occurrence_types"]
        for markov_time in pp_configs["markov_times"]
        for consensus in pp_configs["consensus"]
        for seed in pp_configs["seeds"]
        for number_of_modules in pp_configs["numbers_of_modules"]
        for method in pp_configs["methods"]
    ]

    # Check if source graphs exist
    existing_source_files = set(list_dir(source_folder, source_file_ext))
    required_source_files = {
        filename_for_pp_config(
            **{
                **item,
                "seed": None,
                "markov_time": None,
                "number_of_modules": None,
                "consensus": None,
                "method": None,
            },
            file_ext=source_file_ext,
        )
        for item in items
    }
    missing_source_files = required_source_files - existing_source_files
    if len(missing_source_files):
        raise Exception(
            f'Source preprocessed graphs are missing: {" ".join(sorted(missing_source_files))}'
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


def cd_cluster(config, source_folder, target_folder):
    source_filename = filename_for_pp_config(
        **{
            **config,
            "seed": None,
            "markov_time": None,
            "number_of_modules": None,
            "consensus": None,
            "method": None,
        },
        file_ext=source_file_ext,
    )
    g = nx.read_gpickle(f"{source_folder}/{source_filename}")

    g = compile_source_graph(g, config["method"])

    if not config["consensus"]:
        clustering, D = cluster(g, config, return_tree=True)

        tree_path = (
            target_folder
            + "/"
            + filename_for_pp_config(**config, file_ext=".gpickle.gz")
        )
        nx.write_gpickle(D, tree_path)

    else:
        clustering = consensus_clustering(g, config)
        target_filename = filename_for_pp_config(**config, file_ext="target_file_ext")

    clustering = missings_nodes_as_additional_clusters(clustering)

    target_filename = filename_for_pp_config(**config, file_ext=target_file_ext)
    write_community_json(clustering, f"{target_folder}/{target_filename}")


def cluster(g, config, return_tree, seed=None):
    if config["method"].lower() in ["infomap", "infomap-directed"]:
        directed = bool(config["method"].lower() == "infomap-directed")
        return cdlib_custom_algorithms.infomap(
            g,
            markov_time=config["markov_time"],
            seed=seed or config.get("seed"),
            number_of_modules=config.get("number_of_modules"),
            return_tree=return_tree,
            directed=directed,
        )
    elif config["method"].lower() == "louvain":
        return cdlib_custom_algorithms.louvain(
            g,
            weight="weight",
            seed=seed or config.get("seed"),
            resolution=config["markov_time"],
            return_tree=return_tree,
        )
    else:
        raise Exception(f'Method {config["method"]} not allowed')


def compile_source_graph(g, method):
    if method.lower() in ["infomap", "infomap-directed"]:
        return g
    elif method.lower() == "louvain":
        h = nx.Graph()
        h.add_nodes_from(list(g.nodes(data=True)))
        weights = defaultdict(float)
        for u, v, data in g.edges(data=True):
            x, y = sorted([u, v])
            weight_to_add = data["weight"]
            # if data["edge_type"] == "sequence":
            #     weight_to_add = weight_to_add / 2
            weights[(x, y)] += weight_to_add
        h.add_edges_from(list(weights.keys()))
        nx.set_edge_attributes(h, dict(weights), "weight")
        return h
    else:
        raise Exception(f"Method {method} not allowed")


def consensus_clustering(g, config):
    # Activate this section to add noise to cluster weights
    # clustering_orig = cdlib_custom_algorithms.infomap(
    #     g,
    #     markov_time=config["markov_time"],
    #     seed=config.get("seed"),
    #     number_of_modules=config.get("number_of_modules"),
    # )
    # orig_weights = nx.get_edge_attributes(g, "weight")
    # noised_G = g.copy()
    clustering_communities = []
    for idx in range(config["consensus"]):

        # Activate this section to add noise to cluster weights and us noised_G to cluster
        # noisy_weights = {k: np.random.poisson(v) for k, v in orig_weights.items()}
        # nx.set_edge_attributes(noised_G, noisy_weights, "weight")

        seed = config.get("seed") + idx * 10000
        clustering = cluster(g, config, return_tree=False, seed=seed)
        clustering_communities.append(clustering.communities)
        clustering_method_parameters = clustering.method_parameters

    consensus_g = nx.Graph()
    consensus_g.add_nodes_from(g.nodes)
    for communities in clustering_communities:
        for community in communities:
            add_weighted_clique(community, consensus_g)

    min_edge = int(len(clustering_communities) * 0.95)

    edges_below_threshold = [
        (u, v)
        for u, v in consensus_g.edges
        if consensus_g.edges[u, v]["weight"] < min_edge
    ]
    consensus_g.remove_edges_from(edges_below_threshold)
    significant_clusters = list(nx.connected_components(consensus_g))
    significant_clusters = sorted(
        [list(x) for x in significant_clusters], key=lambda x: -len(x)
    )

    # Activate this section to add noise to cluster weights
    # Compare the consensus_g with the original clustering.
    # overlap_communities = [
    #     sorted(
    #         [
    #             community_orig.intersection(community_noisy)
    #             for community_noisy in significant_clusters
    #             if community_orig.intersection(community_noisy)
    #         ],
    #         key=lambda x: -len(x),
    #     )
    #     for community_orig in sorted(
    #         [set(x) for x in clustering_orig.communities], key=lambda x: -len(x)
    #     )
    # ]
    # overlap_stats = [
    #     (sum([len(y) for y in x]), [len(y) for y in x]) for x in overlap_communities
    # ]
    # print('\n'.join([f'{x} {y}' for x, y in overlap_stats]))
    # significant_overlap_clusters = [
    #     overlap_community
    #     for communities_orig in overlap_communities
    #     for overlap_community in communities_orig
    # ]
    #
    # clustering = NodeClustering(
    #     [list(x) for x in significant_overlap_clusters],
    #     g,
    #     "Infomap Smoothed",
    #     method_parameters=clustering_method_parameters,
    # )

    # Deactivate this section to add noise to cluster weights
    clustering = NodeClustering(
        [list(x) for x in significant_clusters],
        g,
        "Infomap Consensus",
        method_parameters=clustering_method_parameters,
    )

    return clustering


def add_weighted_clique(nodes, G):
    for u, v in combinations(nodes, 2):
        if not G.has_edge(u, v):
            G.add_edge(u, v, weight=0)
        G.edges[u, v]["weight"] += 1
