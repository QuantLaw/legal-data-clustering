import networkx as nx
import regex

from legal_data_preprocessing.utils.common import ensure_exists, list_dir
from legal_data_preprocessing.utils.graph_api import (
    hierarchy_graph,
    sequence_graph,
    decay_function,
)
from utils.utils import filename_for_pp_config

target_file_ext = ".gpickle.gz"


def cd_preprocessing_prepare(
    overwrite, snapshots, pp_configs, source_folder, target_folder
):
    ensure_exists(target_folder)
    items = [
        dict(snapshot=snapshot, pp_ratio=pp_ratio, pp_decay=pp_decay, pp_merge=pp_merge)
        for snapshot in snapshots
        for pp_ratio in pp_configs["pp_ratios"]
        for pp_decay in pp_configs["pp_decays"]
        for pp_merge in pp_configs["pp_merges"]
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


def cd_preprocessing(config, source_folder, target_folder):
    source_path = f"{source_folder}/seqitems/{config['snapshot']}.gpickle.gz"
    seq_decay_func = decay_function(config["pp_decay"])

    G = nx.read_gpickle(source_path)
    mqG = quotient_graph_with_merge(G, merge_threshold=config["pp_merge"])
    smqG = sequence_graph(
        mqG, seq_decay_func=seq_decay_func, seq_ref_ratio=config["pp_ratio"]
    )

    target_path = (
        f"{target_folder}/{filename_for_pp_config(**config, file_ext=target_file_ext)}"
    )
    nx.write_gpickle(smqG, target_path)


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

    return nG


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
