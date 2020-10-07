import json
import os
import pickle
from collections import Counter, defaultdict

import networkx as nx
from cdlib import readwrite
from quantlaw.utils.files import ensure_exists, list_dir

from clustering_utils.utils import filename_for_pp_config


def cd_cluster_evolution_graph_prepare(
    overwrite,
    cluster_mapping_configs,
    source_folder,
    snaphot_mapping_folder,
    subseqitem_mapping_folder,
    target_folder,
):
    ensure_exists(target_folder)

    # get configs
    configs = [
        dict(
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
        for pp_ratio in cluster_mapping_configs["pp_ratios"]
        for pp_decay in cluster_mapping_configs["pp_decays"]
        for pp_merge in cluster_mapping_configs["pp_merges"]
        for pp_co_occurrence in cluster_mapping_configs["pp_co_occurrences"]
        for pp_co_occurrence_type in cluster_mapping_configs["pp_co_occurrence_types"]
        for markov_time in cluster_mapping_configs["markov_times"]
        for consensus in cluster_mapping_configs["consensus"]
        for seed in cluster_mapping_configs["seeds"]
        for number_of_modules in cluster_mapping_configs["numbers_of_modules"]
        for method in cluster_mapping_configs["methods"]
    ]

    # Check if clusterings exist
    for config in configs:
        config_clustering_files, snapshots = get_config_clustering_files(
            config, source_folder
        )

        mapping_files = list_dir(snaphot_mapping_folder, ".json")
        for snapshot1, snapshot2 in zip(snapshots[:-1], snapshots[1:]):
            mapping_file = f"{snapshot1}_{snapshot2}.json"
            if mapping_file not in mapping_files:
                raise Exception(f"mapping {mapping_file} is missing")

        mapping_files = list_dir(subseqitem_mapping_folder, ".pickle")
        for snapshot in snapshots:
            mapping_file = f'{snapshot}_{config["pp_merge"]}.pickle'
            if mapping_file not in mapping_files:
                raise Exception(f"mapping {mapping_file} is missing")

    existing_files = set(list_dir(target_folder, ".gpickle.gz"))
    if not overwrite:
        configs = [
            config
            for config in configs
            if filename_for_pp_config(snapshot="all", **config, file_ext=".gpickle.gz")
            not in existing_files
        ]

    return configs


def cd_cluster_evolution_graph(
    config,
    source_folder,
    snaphot_mapping_folder,
    subseqitem_mapping_folder,
    target_folder,
    dataset,
):
    config_clustering_files, snapshots = get_config_clustering_files(
        config, source_folder
    )

    first = True

    B = nx.DiGraph()

    for config_clustering_file, snapshot in zip(config_clustering_files, snapshots):
        # Add nodes to graph

        clustering = readwrite.read_community_json(
            os.path.join(source_folder, config_clustering_file)
        )

        with open(
            os.path.join(
                subseqitem_mapping_folder, f'{snapshot}_{config["pp_merge"]}.pickle'
            ),
            "rb",
        ) as f:
            preprocessed_mappings = pickle.load(f)

        counters_dict = get_cluster_law_names_counting_seqitems(
            preprocessed_mappings, clustering.communities
        )
        most_common_dict = {
            k: ",".join([f"{elem_k},{count}" for elem_k, count in v.most_common()])
            for k, v in counters_dict.items()
        }
        chars_n_dict = get_community_sizes(
            clustering.communities, preprocessed_mappings["chars_n"]
        )
        tokens_n_dict = get_community_sizes(
            clustering.communities, preprocessed_mappings["tokens_n"]
        )

        for community_key, community_nodes in enumerate(clustering.communities):
            community_nodes_sorted = sorted(
                community_nodes,
                key=lambda n: preprocessed_mappings["tokens_n"][n],
                reverse=True,
            )
            for n in community_nodes_sorted:
                assert "," not in n
            B.add_node(
                f"{snapshot}_{community_key}",
                bipartite=snapshot,
                chars_n=chars_n_dict[community_key],
                tokens_n=tokens_n_dict[community_key],
                law_names=most_common_dict[community_key],
                nodes_contained=",".join(community_nodes_sorted),
            )

        communities_rolled_down = [
            [
                n
                for rolled_up_node in community_nodes
                for n in preprocessed_mappings["subseqitems_mapping"][rolled_up_node]
            ]
            for community_nodes in clustering.communities
        ]

        community_id_for_rolled_down = {
            n: community_id
            for community_id, nodes in enumerate(communities_rolled_down)
            for n in nodes
        }

        if not first:

            with open(f"{snaphot_mapping_folder}/{prev_snapshot}_{snapshot}.json") as f:
                mapping = json.load(f)

            # draw edges
            edges_tokens_n = defaultdict(int)
            edges_charns_n = defaultdict(int)
            for prev_leaf, leaf in mapping.items():
                try:
                    prev_community_id = prev_community_id_for_rolled_down[prev_leaf]
                except KeyError as err:
                    report_mapping_error(err, prev_preprocessed_mappings["tokens_n"])
                    continue

                try:
                    community_id = community_id_for_rolled_down[leaf]
                except KeyError as err:
                    report_mapping_error(err, preprocessed_mappings["tokens_n"])
                    continue

                prev_community_name = f"{prev_snapshot}_{prev_community_id}"
                community_name = f"{snapshot}_{community_id}"
                edge = (prev_community_name, community_name)

                # Use the tokens_n and chars_n values of the later year
                edges_tokens_n[edge] += preprocessed_mappings["tokens_n"][leaf]
                edges_charns_n[edge] += preprocessed_mappings["chars_n"][leaf]

            B.add_edges_from(edges_tokens_n.keys())
            nx.set_edge_attributes(B, edges_tokens_n, "tokens_n")
            nx.set_edge_attributes(B, edges_charns_n, "chars_n")

        first = False
        prev_snapshot = snapshot
        prev_community_id_for_rolled_down = community_id_for_rolled_down
        prev_preprocessed_mappings = preprocessed_mappings

    nx.write_gpickle(
        B,
        f"{target_folder}/"
        f'{filename_for_pp_config(snapshot="all", **config, file_ext=".gpickle.gz")}',
    )


def get_cluster_law_names_counting_seqitems(preprocessed_mappings, communities):
    counters = dict()
    for community_id, community_nodes in enumerate(communities):
        counters[community_id] = Counter(
            [
                "_".join(community_node.split("_")[:-1])
                for community_node in community_nodes
                for _ in range(
                    preprocessed_mappings["seqitem_counts"].get(community_node, 0)
                )
            ]
        )
    return counters


def get_config_clustering_files(config, source_folder):
    """
    get all clusterings for a given config. (Multiple snapshots to be mapped)
    ::return filenames, snapshots
    """
    existing_clustering = set(list_dir(source_folder, ".json"))
    config_filename_part = filename_for_pp_config(
        snapshot="", **config, file_ext=".json"
    )
    config_clustering_files = sorted(
        [x for x in existing_clustering if x.endswith(config_filename_part)]
    )
    snapshots = sorted(
        [
            config_clustering_file.split("_")[0]
            for config_clustering_file in config_clustering_files
        ]
    )
    return config_clustering_files, snapshots


def get_community_sizes(communities, node_sizes):
    community_sizes = dict()
    for community_id, nodes in enumerate(communities):
        community_sizes[community_id] = sum([node_sizes[n] for n in nodes])
    return community_sizes


def report_mapping_error(err, tokens_n_dict):
    err_tokens_n = tokens_n_dict[err.args[0]]
    if err_tokens_n:
        print(err.args[0], "not found and has", err_tokens_n, "tokens")
