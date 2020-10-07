import os
import pickle
from bisect import bisect_left
from collections import defaultdict

import networkx as nx

from clustering_utils.utils import ensure_exists, list_dir
from clustering_utils.graph_api import hierarchy_graph
from clustering_utils.nodes_merging import quotient_graph_with_merge


def filename_for_mapping(mapping):
    return f'{mapping["snapshot"]}_{mapping["pp_merge"]}.pickle'


def cd_cluster_evolution_mappings_prepare(
    overwrite, cluster_mapping_configs, source_folder, target_folder
):
    ensure_exists(target_folder)

    subseqitems_snapshots = [
        f.split(".")[0]
        for f in list_dir(f"{source_folder}/subseqitems/", ".gpickle.gz")
    ]

    # get configs
    mappings = [
        dict(pp_merge=pp_merge, snapshot=subseqitems_snapshot,)
        for pp_merge in cluster_mapping_configs["pp_merges"]
        for subseqitems_snapshot in subseqitems_snapshots
    ]

    existing_files = set(list_dir(target_folder, ".pickle"))
    if not overwrite:
        mappings = [
            mapping
            for mapping in mappings
            if filename_for_mapping(mapping) not in existing_files
        ]

    return sorted(mappings, key=str)


def cd_cluster_evolution_mappings(item, source_folder, target_folder, dataset):
    seqitems_path = os.path.join(
        source_folder, "seqitems", item["snapshot"] + ".gpickle.gz"
    )
    subseqitems_path = os.path.join(
        source_folder, "subseqitems", item["snapshot"] + ".gpickle.gz"
    )

    merged_nodes, node_seqitem_counts = get_merged_nodes(
        seqitems_path, item["pp_merge"]
    )

    G = nx.read_gpickle(subseqitems_path)
    hierarchy_G = hierarchy_graph(G)
    hierarchy_G_degrees = dict(hierarchy_G.out_degree())

    leaves = [n for n, degree in hierarchy_G_degrees.items() if degree == 0]

    merged_nodes = sorted(merged_nodes)
    merged_nodes_leaves = [
        n
        for n in merged_nodes
        if not any(successor in merged_nodes for successor in hierarchy_G.successors(n))
    ]
    merged_nodes_descendants = {
        descendant
        for n in merged_nodes_leaves
        for descendant in nx.descendants(hierarchy_G, n)
    }
    subseqitems_mapping = {n: list() for n in merged_nodes}
    for leaf in leaves:
        if leaf in merged_nodes_descendants:
            parent_node = find_lt(merged_nodes, leaf)
            subseqitems_mapping[parent_node].append(leaf)
            assert parent_node in nx.ancestors(hierarchy_G, leaf), (
                parent_node,
                leaf,
                nx.ancestors(hierarchy_G, leaf),
                set(nx.ancestors(hierarchy_G, leaf)) & merged_nodes_descendants,
            )

    prepared_data = dict(
        subseqitems_mapping=subseqitems_mapping,
        tokens_n=dict(nx.get_node_attributes(G, "tokens_n")),
        chars_n=dict(nx.get_node_attributes(G, "chars_n")),
        seqitem_counts=node_seqitem_counts,
    )

    with open(os.path.join(target_folder, filename_for_mapping(item)), "wb") as f:
        pickle.dump(prepared_data, f)


def find_lt(a, x):
    "Find rightmost value less than x"
    i = bisect_left(a, x)
    if i:
        return a[i - 1]
    raise ValueError


def get_merged_nodes(seqitems_path, pp_merge):
    seqitems_path = seqitems_path
    G = nx.read_gpickle(seqitems_path)
    Gm, nodes_mapping = quotient_graph_with_merge(G, merge_threshold=pp_merge)

    nodes_mapping_inversed = defaultdict(list)
    for node, parent in nodes_mapping.items():
        if G.nodes[node]["level"] != -1 and G.nodes[node]["type"] == "seqitem":
            nodes_mapping_inversed[parent].append(node)

    node_seqitem_counts = {n: len(v) for n, v in nodes_mapping_inversed.items()}

    return sorted(set(nodes_mapping.values())), node_seqitem_counts
