###################
# Merge graph nodes
###################
import networkx as nx
import regex

from legal_data_preprocessing.utils.graph_api import hierarchy_graph


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
