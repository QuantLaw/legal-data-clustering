import os
import pickle
import re
from collections import Counter

import networkx as nx
import pandas as pd

from quantlaw.utils.files import ensure_exists, list_dir


def filename_for_mapping(mapping):
    return f'{mapping["snapshot"]}_{mapping["pp_merge"]}.pickle'


def cd_cluster_evolution_mappings_prepare(
    overwrite, cluster_mapping_configs, source_folder, target_folder, snapshots
):
    ensure_exists(target_folder)

    subseqitems_snapshots = [
        f.split(".")[0]
        for f in list_dir(f"{source_folder}/", ".edges.csv.gz")
    ] # fix

    if snapshots:
        subseqitems_snapshots = [
            s
            for s in subseqitems_snapshots
            if s in snapshots
        ]

    # get configs
    mappings = [
        dict(
            pp_merge=pp_merge,
            snapshot=subseqitems_snapshot,
        )
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


def cd_cluster_evolution_mappings(item, source_folder, preprocessed_graph_folder, target_folder):
    pattern = re.compile(
        re.escape(item["snapshot"]) +
        r'_[0-9\-]+_[0-9\-]+_' +
        re.escape(str(item["pp_merge"]).replace(".", "-") + '.gpickle.gz')
    )
    filenames = sorted([
        filename
        for filename in os.listdir(preprocessed_graph_folder)
        if pattern.fullmatch(filename)
    ])
    if len(filenames) > 1:
        print('Found multiple matching preprocessed graphs. Taking', filenames[0])
    elif not filenames:
        raise Exception('Not preprocessed graphs found for', pattern)
    filename = filenames[0]

    G = nx.read_gpickle(os.path.join(
        preprocessed_graph_folder, filename
    ))
    cluster_level_nodes = set(G.nodes())
    del G

    df_nodes = pd.read_csv(os.path.join(
        source_folder,
        item["snapshot"] + '.nodes.csv.gz'
    ), dtype={'texts_tokens_n': str, "texts_chars_n": str})
    df_edges = pd.read_csv(os.path.join(
        source_folder,
        item["snapshot"] + '.edges.csv.gz'
    ))
    containment_edges = df_edges[df_edges.edge_type == 'containment']
    parents = {v: u for v, u in zip(containment_edges.v, containment_edges.u)}

    items_mapping = {k: [] for k in cluster_level_nodes}

    for key in df_nodes.key:
        contracted_to = get_contracted_node(key, parents, cluster_level_nodes)
        if contracted_to:
            items_mapping[contracted_to].append(key)

    node_seqitem_counts = Counter(
        get_contracted_node(key, parents, cluster_level_nodes)
        for key in df_nodes[df_nodes.type == 'seqitem'].key
    )
    node_seqitem_counts = dict(node_seqitem_counts)

    tokens_n = {
        k: v
        for k, v in zip(df_nodes.key, df_nodes.tokens_n)
        if not pd.isna(v)
    }
    chars_n = {
        k: v
        for k, v in zip(df_nodes.key, df_nodes.chars_n)
        if not pd.isna(v)
    }
    # Details of the size of the children if a child of a node is a text and
    # the node has more than one child
    texts_tokens_n = {
        k: list(map(int, v.split(',')))
        for k, v in zip(df_nodes.key, df_nodes.texts_tokens_n)
        if not pd.isna(v)
    }
    texts_chars_n = {
        k: list(map(int, v.split(',')))
        for k, v in zip(df_nodes.key, df_nodes.texts_chars_n)
        if not pd.isna(v)
    }
    document_type = {
        k: v
        for k, v in zip(df_nodes.key, df_nodes.document_type)
        if not pd.isna(v)
    }


    prepared_data = dict(
        items_mapping=items_mapping,
        tokens_n=tokens_n,
        chars_n=chars_n,
        seqitem_counts=node_seqitem_counts,
        texts_tokens_n=texts_tokens_n,
        texts_chars_n=texts_chars_n,
        document_type=document_type,
    )

    with open(
        os.path.join(target_folder, filename_for_mapping(item)), "wb"
    ) as f:
        pickle.dump(prepared_data, f)


def get_contracted_node(node, parents, cluster_level_nodes):
    if node in cluster_level_nodes:
        return node
    parent = parents.get(node)
    if parent is None:
        return None
    else:
        return get_contracted_node(parent, parents, cluster_level_nodes)

def nodes_with_parents(nodes, parents):
    nodes = list(nodes)
    idx = 0
    while idx < len(nodes):
        parent = parents.get(nodes[idx])
        if parent and parent not in nodes:
            nodes.append(parent)
        idx += 1
    return nodes