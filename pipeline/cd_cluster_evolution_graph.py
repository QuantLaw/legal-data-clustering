import json

import networkx as nx

from legal_data_preprocessing.utils.common import (
    ensure_exists,
    list_dir,
)
from utils.graph_api import (
    get_clustering_result,
    get_community_ids,
    get_leaves_with_communities,
    get_community_law_name_counters,
    add_community_to_graph,
)
from utils.utils import filename_for_pp_config


def cd_cluster_evolution_graph_prepare(
    overwrite, cluster_mapping_configs, source_folder, mapping_folder, target_folder
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

        mapping_files = list_dir(mapping_folder, ".json")
        for snapshot1, snapshot2 in zip(snapshots[:-1], snapshots[1:]):
            mapping_file = f"{snapshot1}_{snapshot2}.json"
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
    config, source_folder, mapping_folder, target_folder, dataset
):
    config_clustering_files, snapshots = get_config_clustering_files(
        config, source_folder
    )

    first = True

    B = nx.DiGraph()

    for config_clustering_file, snapshot in zip(config_clustering_files, snapshots):
        # Add nodes to graph
        clustering = get_clustering_result(
            f"{source_folder}/{config_clustering_file}",
            dataset,
            graph_type="subseqitems",
        )
        add_community_to_graph(clustering)

        # TODO integrate more stats
        counters_dict = get_community_law_name_counters(clustering, "seqitems")
        most_common_dict = {
            k: ",".join([f"{elem_k},{count}" for elem_k, count in v.most_common()])
            for k, v in counters_dict.items()
        }
        chars_n_dict = get_community_sizes(clustering, "chars_n")
        tokens_n_dict = get_community_sizes(clustering, "tokens_n")

        for community_key in get_community_ids(clustering):
            B.add_node(
                f"{snapshot}_{community_key}",
                bipartite=snapshot,
                chars_n=chars_n_dict[community_key],
                tokens_n=tokens_n_dict[community_key],
                law_names=most_common_dict[community_key],
            )

        if not first:

            # Add edges
            with open(f"{mapping_folder}/{prev_snapshot}_{snapshot}.json") as f:
                mapping = json.load(f)

            # Get nodes with cluster membership
            prev_orig_communities = get_leaves_with_communities(prev_clustering.graph)
            prev_mapped_communities = map_dict_keys(prev_orig_communities, mapping)
            print("prev_mapped_communities", len(prev_mapped_communities))
            orig_communities = get_leaves_with_communities(clustering.graph)
            print("orig_communities", len(orig_communities))

            intersecting_nodes = set(prev_mapped_communities.keys()).intersection(
                set(orig_communities.keys())
            )

            # print(sorted({k for k in prev_mapped_communities.keys() if k not in orig_communities.keys()})[:1000])
            if not len(prev_mapped_communities) == len(intersecting_nodes):
                print(
                    f"WARNING: prev_mapped_communities and intersecting_nodes do not match: \n"
                    f"{len(prev_mapped_communities)} != {len(intersecting_nodes)}"
                )
            # TODO replace the warning above (starting from 'if') with this assert and
            #  make sure that prev_mapped_communities matches intersecting_nodes
            # assert len(prev_mapped_communities) == len(
            #     intersecting_nodes
            # ), f"{len(prev_mapped_communities)} != {len(intersecting_nodes)}"

            # draw edges
            for node in intersecting_nodes:
                prev_community = f"{prev_snapshot}_{prev_mapped_communities[node][0]}"
                community = f"{snapshot}_{orig_communities[node][0]}"
                if not B.has_edge(prev_community, community):
                    B.add_edge(prev_community, community, chars_n=0, tokens_n=0)

                B.edges[prev_community, community]["chars_n"] += clustering.graph.nodes[
                    node
                ]["chars_n"]
                B.edges[prev_community, community][
                    "tokens_n"
                ] += clustering.graph.nodes[node]["tokens_n"]
                # B.edges[prev_community, community][f"{graph_type}_n"] += 1

        first = False
        prev_clustering = clustering
        prev_snapshot = snapshot

    nx.write_gpickle(
        B,
        f"{target_folder}/"
        f'{filename_for_pp_config(snapshot="all", **config, file_ext=".gpickle.gz")}',
    )


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


def map_dict_keys(source_dict, mapping):
    return {mapping[k]: v for k, v in source_dict.items() if k in mapping}


def get_community_sizes(clustering, size_attribute="chars_n"):
    community_sizes = dict()
    for community_id, nodes in enumerate(clustering.communities):
        community_sizes[community_id] = sum(
            [clustering.graph.nodes[n][size_attribute] for n in nodes]
        )
    return community_sizes
