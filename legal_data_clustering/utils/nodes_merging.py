import networkx as nx
import regex

from quantlaw.utils.networkx import hierarchy_graph


def quotient_graph_with_merge(
    G, self_loops=False, merge_threshold=0, merge_attribute="chars_n"
):
    """
    Generate the quotient graph, recursively merging nodes if the merge result
    does not exceed merge threshold.
    or merge threshold 0 this rolls up all node whose siblings are exclusively
    nodes with merge attribute value 0.
    """

    hG = hierarchy_graph(G)

    # build a new MultiDiGraph
    nG = nx.MultiDiGraph()

    # create a mapping especially for contracted nodes
    # to draw edges between the remaining nodes appropriately
    nodes_mapping = {}

    for node_id, node_attrs in G.nodes(data=True):

        if is_node_contracted(hG, node_id, merge_threshold, merge_attribute):
            # Add node to mapping to draw correct edges between contracted nodes
            # print(f"-", end="")
            merge_parent = get_merge_parent(
                hG, node_id, merge_threshold, merge_attribute
            )
            nodes_mapping[node_id] = merge_parent
        else:
            # Add node to new graph and add node to mapping for convenience
            # print(f"+", end="")
            nG.add_node(node_id, **node_attrs)
            nodes_mapping[node_id] = node_id

    for e_source, e_target, e_data in G.edges(data=True):
        if e_data["edge_type"] in {"reference", "authority"}:
            # get source and target of edge in quotient graph
            source = nodes_mapping[e_source]
            target = nodes_mapping[e_target]
            if self_loops or source != target:  # skip loops, if deactivated
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


chapter_buch_pattern = regex.compile(
    r"\w*\s*\bBuch\b|\[?CHAPTER|\[?Chapter|\[?Chap\."
)

def is_root_node(G, node):
    """
    Helper for is_node_contracted
    """
    return G.in_degree(node) == 0


def is_child_of_root_node(G, node):
    """
    Helper for is_node_contracted
    """
    parent = list(G.predecessors(node))[0]
    return G.in_degree(parent) == 0


def is_book_or_chapter(G, node):
    """
    Helper for is_node_contracted
    """
    return "heading" in G.nodes[node] and chapter_buch_pattern.match(
        G.nodes[node]["heading"]
    )


def has_book_or_chapter_above(G, node):
    """
    Helper for is_node_contracted
    """
    matching_ancestors = [
        n
        for n in nx.ancestors(G, node)
        if n != "root"
        and "heading" in G.nodes[n]
        and chapter_buch_pattern.match(G.nodes[n]["heading"])
    ]
    return bool(matching_ancestors)


def has_book_or_chapter_below(G, node):
    """
    Helper for is_node_contracted

    Note that nx.predecessor returns a dictionary of nodes on a path from
    node to all other nodes, i.e., the dictionary's keys are the descendants
    (possibly replaced by nx.descendants in the future).
    """
    matching_descendants = [
        n
        for n in nx.predecessor(G, node)
        if n != "root"
        and "heading" in G.nodes[n]
        and chapter_buch_pattern.match(G.nodes[n]["heading"])
    ]
    return bool(matching_descendants)


def is_parent_too_big(G, node, merge_attribute, merge_threshold):
    """
    Helper for is_node_contracted
    """
    parent = list(G.predecessors(node))[0]
    return G.nodes[parent][merge_attribute] > merge_threshold


def check_chapters(G, node):
    """
    Helper for is_node_contracted
    """
    if is_book_or_chapter(G, node):
        return False
    elif has_book_or_chapter_above(G, node):
        return True
    else:  # chapter below or no chapter or book in branch
        return False


def is_node_contracted(G, node, merge_threshold=0, merge_attribute="chars_n"):
    """
    Determine whether a node should be in the quotient graph.
    In this implementation, nodes and their siblings are contracted
    if the parent they are contracted in is still below a certain threshold.
    It would also be possible to contract a node and its siblings if one node
    is below a certain threshold but the parent would be above the threshold.
    :param G: hierarchical graph
    :param node: current node name
    :param merge_threshold:
    :param merge_attribute:
    :return: boolean
    """
    if is_root_node(G, node) or is_child_of_root_node(G, node):
        return False
    elif merge_threshold == -1:
        return check_chapters(G, node)
    elif is_parent_too_big(G, node, merge_attribute, merge_threshold):
        return False
    else:
        return True
