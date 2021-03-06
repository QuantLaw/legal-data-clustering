import json
import os
import pickle
from collections import Counter, defaultdict

import networkx as nx
from cdlib import readwrite
from quantlaw.utils.files import ensure_exists, list_dir

from legal_data_clustering.utils.config_handling import get_configs
from legal_data_clustering.utils.config_parsing import filename_for_pp_config
from legal_data_clustering.utils.graph_api import cluster_families


def cd_cluster_evolution_graph_prepare(
    overwrite,
    cluster_mapping_configs,
    source_folder,
    snaphot_mapping_folder,
    subseqitem_mapping_folder,
    target_folder,
):
    ensure_exists(target_folder)
    configs = get_configs(cluster_mapping_configs)

    # Check if clusterings exist
    for config in configs:
        config_clustering_files, snapshots = get_config_clustering_files(
            config, source_folder
        )

        mapping_files = list_dir(snaphot_mapping_folder, ".json")
        check_mapping_files(mapping_files, snapshots, config, ".json")

        mapping_files = list_dir(subseqitem_mapping_folder, ".pickle")
        check_mapping_files(mapping_files, snapshots, config, ".pickle")

    existing_files = set(list_dir(target_folder, ".gpickle.gz"))
    if not overwrite:
        get_configs_no_overwrite(configs, existing_files)

    return configs


def cd_cluster_evolution_graph(
    config,
    source_folder,
    snaphot_mapping_folder,
    subseqitem_mapping_folder,
    target_folder,
    regulations,
):
    config_clustering_files, snapshots = get_config_clustering_files(
        config, source_folder
    )

    first = True

    B = nx.DiGraph()

    prev_community_id_for_rolled_down = None
    prev_preprocessed_mappings = None
    prev_snapshot = None

    for config_clustering_file, snapshot in zip(config_clustering_files, snapshots):
        # Add nodes to graph

        clustering = readwrite.read_community_json(
            os.path.join(source_folder, config_clustering_file)
        )

        with open(
            os.path.join(
                subseqitem_mapping_folder,
                f'{snapshot}_{config["pp_merge"]}.pickle',
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
            clustering.communities,
            preprocessed_mappings["chars_n"],
        )
        tokens_n_dict = get_community_sizes(
            clustering.communities, preprocessed_mappings["tokens_n"]
        )

        for community_key, community_nodes in enumerate(clustering.communities):
            community_nodes_sorted = sorted(
                community_nodes,
                key=lambda n: preprocessed_mappings["tokens_n"].get(n, 0),
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
                for n in preprocessed_mappings["items_mapping"][rolled_up_node]
            ]
            for community_nodes in clustering.communities
        ]

        community_id_for_rolled_down = {
            n: community_id
            for community_id, nodes in enumerate(communities_rolled_down)
            for n in nodes
        }

        if not first:

            with open(
                os.path.join(snaphot_mapping_folder, f"{prev_snapshot}_{snapshot}.json")
            ) as f:
                mapping = json.load(f)

            # draw edges
            edges_tokens_n = defaultdict(int)
            edges_chars_n = defaultdict(int)
            for prev_leaf_and_text_idx, leaf_and_text_idx in mapping.items():
                prev_leaf, prev_text_idx = prev_leaf_and_text_idx.rsplit("_", 1)
                leaf, text_idx = leaf_and_text_idx.rsplit("_", 1)

                text_idx = int(text_idx)

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

                if leaf in preprocessed_mappings["texts_tokens_n"]:
                    texts_tokens_n = preprocessed_mappings["texts_tokens_n"][leaf]
                    texts_chars_n = preprocessed_mappings["texts_chars_n"][leaf]
                    tokens_n = texts_tokens_n[text_idx]
                    chars_n = texts_chars_n[text_idx]
                else:
                    assert text_idx == 0
                    tokens_n = preprocessed_mappings["tokens_n"][leaf]
                    chars_n = preprocessed_mappings["chars_n"][leaf]

                # Use the tokens_n and chars_n values of the later year
                edges_tokens_n[edge] += tokens_n
                edges_chars_n[edge] += chars_n

            B.add_edges_from(edges_tokens_n.keys())
            nx.set_edge_attributes(B, edges_tokens_n, "tokens_n")
            nx.set_edge_attributes(B, edges_chars_n, "chars_n")

        first = False
        prev_snapshot = snapshot
        prev_community_id_for_rolled_down = community_id_for_rolled_down
        prev_preprocessed_mappings = preprocessed_mappings

    nx.write_gpickle(
        B,
        f"{target_folder}/"
        f'{filename_for_pp_config(snapshot="all", **config, file_ext=".gpickle.gz")}',
    )

    # Write families
    families = cluster_families(B, threshold=0.15)
    path = (
        f"{target_folder}/"
        f'{filename_for_pp_config(snapshot="all", **config, file_ext=".families.json")}'
    )
    with open(path, "w") as f:
        json.dump(families, f)


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


def check_mapping_files(mapping_files, snapshots, config, ending):
    if ending == ".json":
        for snapshot1, snapshot2 in zip(snapshots[:-1], snapshots[1:]):
            mapping_file = f"{snapshot1}_{snapshot2}.json"
            if mapping_file not in mapping_files:
                raise Exception(f"mapping {mapping_file} is missing")
    elif ending == ".pickle":
        for snapshot in snapshots:
            mapping_file = f'{snapshot}_{config["pp_merge"]}.pickle'
            if mapping_file not in mapping_files:
                raise Exception(f"mapping {mapping_file} is missing")
    else:
        raise Exception(f"Invalid ending '{ending}' (use '.json'|'.pickle')!")


def get_configs_no_overwrite(configs, existing_files):
    configs = [
        config
        for config in configs
        if filename_for_pp_config(snapshot="all", **config, file_ext=".gpickle.gz")
        not in existing_files
    ]
    return configs


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
        community_sizes[community_id] = sum([node_sizes.get(n, 0) for n in nodes])
    return community_sizes


def report_mapping_error(err, tokens_n_dict):
    err_tokens_n = tokens_n_dict[err.args[0]]
    if err_tokens_n:
        print(err.args[0], "not found and has", err_tokens_n, "tokens")
