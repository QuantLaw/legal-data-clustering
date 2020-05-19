import itertools

import infomap as imp
from cdlib import NodeClustering
from cdlib.utils import convert_graph_formats
import networkx as nx
from collections import defaultdict
import community as louvain_modularity
from community import generate_dendrogram, partition_at_level


def infomap(
    g,
    seed=None,
    options="--inner-parallelization --silent",
    markov_time=1.0,
    number_of_modules=None,
    return_tree=False,
):
    """
    Infomap is based on ideas of information theory.
    The algorithm uses the probability flow of random walks on a network as a proxy for information flows in the real system and it decomposes the network into modules by compressing a description of the probability flow.

    :param g: a networkx/igraph object
    :return: NodeClustering object

    :Example:

    >>> from cdlib import algorithms
    >>> import networkx as nx
    >>> G = nx.karate_club_graph()
    >>> coms = algorithms.infomap(G)

    :References:

    Rosvall M, Bergstrom CT (2008) `Maps of random walks on complex networks reveal community structure. <https://www.pnas.org/content/105/4/1118/>`_ Proc Natl Acad SciUSA 105(4):1118–1123

    .. note:: Reference implementation: https://pypi.org/project/infomap/
    """

    if imp is None:
        raise ModuleNotFoundError(
            "Optional dependency not satisfied: install infomap to use the selected feature."
        )

    g = convert_graph_formats(g, nx.Graph)

    g1 = nx.convert_node_labels_to_integers(g, label_attribute="name")
    name_map = nx.get_node_attributes(g1, "name")
    coms_to_node = defaultdict(list)

    options_compiled = options + f" --markov-time {markov_time}"
    if number_of_modules:
        options_compiled += f" --preferred-number-of-modules {number_of_modules}"
    if seed:
        options_compiled += f" --seed {seed}"

    # try:
    # with pipes() as (stdout, stderr):
    im = imp.Infomap(options_compiled)
    for u, v, data in g1.edges(data=True):
        im.add_link(u, v, weight=data["weight"])
    im.run()

    for depth in range(1, im.maxTreeDepth()):
        coms_to_node = defaultdict(list)
        for node in im.iterTree():
            # https://mapequation.github.io/infomap/
            # Guess: maxClusterLevel == moduleIndexLevel
            # moduleIndexLevel : int
            # The depth from the root on which to advance the moduleIndex accessed from the iterator for a tree with multiple levels
            # Set to 1 to have moduleIndex() return the coarsest level (top modules), set to 2 for second level modules, and -1 (default) for the finest level of modules (bottom level)
            if node.isLeaf():
                nid = node.physicalId
                # module = node.moduleIndex()
                module = node.path[:depth]
                nm = name_map[nid]
                coms_to_node[module].append(nm)

        # TODO conditionally roll down the treee currently not used,
        #  because 'preferred-number-of-modules' is the preferred method
        break
        # if len(coms_to_node) >= 30:  # TODO param instead of fixed value
        #     break
        # else:
        #     print(
        #         f"At level {depth} of clustering only {len(coms_to_node)}. Consider one level more."
        #     )
    # except:
    #     print(stdout.read())
    #     raise

    coms_infomap = [list(c) for c in coms_to_node.values()]

    clustering = NodeClustering(
        coms_infomap, g, "Infomap", method_parameters={"options": options, "seed": seed}
    )

    if not return_tree:
        return clustering
    else:
        # Create a cluster tree
        D = nx.DiGraph()

        D.add_nodes_from(g.nodes(data=True))

        for node in im.iterTree(maxClusterLevel=-1):
            if node.isRoot():
                D.add_node("root")
            else:
                if node.isLeaf():
                    node_key = g1.nodes[node.physicalId]["name"]
                else:
                    node_key = "tree_" + "_".join(node.path)
                    D.add_node(node_key)

                if len(node.path) == 1:
                    parent_key = "root"
                else:
                    parent_key = "tree_" + "_".join(node.path[:-1])

                assert D.has_node(parent_key)
                D.add_edge(parent_key, node_key)

        _sum_attrs_in_tree(D)

        return clustering, D


def louvain(g, weight="weight", resolution=1.0, seed=None, return_tree=False):
    """
    Louvain  maximizes a modularity score for each community.
    The algorithm optimises the modularity in two elementary phases:
    (1) local moving of nodes;
    (2) aggregation of the network.
    In the local moving phase, individual nodes are moved to the community that yields the largest increase in the quality function.
    In the aggregation phase, an aggregate network is created based on the partition obtained in the local moving phase.
    Each community in this partition becomes a node in the aggregate network. The two phases are repeated until the quality function cannot be increased further.

    :param g: a networkx/igraph object
    :param weight: str, optional the key in graph to use as weight. Default to 'weight'
    :param resolution: double, optional  Will change the size of the communities, default to 1.
    :param randomize:  boolean, optional  Will randomize the node evaluation order and the community evaluation  order to get different partitions at each call, default False
    :return: NodeClustering object


    :Example:

    >>> from cdlib import algorithms
    >>> import networkx as nx
    >>> G = nx.karate_club_graph()
    >>> coms = algorithms.louvain(G, weight='weight', resolution=1., randomize=False)

    :References:

    Blondel, Vincent D., et al. `Fast unfolding of communities in large networks. <https://iopscience.iop.org/article/10.1088/1742-5468/2008/10/P10008/meta/>`_ Journal of statistical mechanics: theory and experiment 2008.10 (2008): P10008.

    .. note:: Reference implementation: https://github.com/taynaud/python-louvain
    """

    g = convert_graph_formats(g, nx.Graph)

    dendo = generate_dendrogram(
        g, weight=weight, resolution=resolution, random_state=seed
    )
    coms = partition_at_level(dendo, len(dendo) - 1)

    # Reshaping the results
    coms_to_node = defaultdict(list)
    for n, c in coms.items():
        coms_to_node[c].append(n)

    coms_louvain = [list(c) for c in coms_to_node.values()]
    clustering = NodeClustering(
        coms_louvain,
        g,
        "Louvain",
        method_parameters={
            "weight": weight,
            "resolution": resolution,
            "random_state": seed,
        },
    )

    if not return_tree:
        return clustering

    else:
        # Create a cluster tree
        D = nx.DiGraph()
        D.add_node("root")
        D.add_nodes_from(g.nodes(data=True))

        graph_key_for_nr = dict()

        for level, level_data in enumerate(reversed(dendo)):
            for nr, parent_nr in level_data.items():
                if level == 0:
                    parent_key = "root"
                    node_path = "tree"
                else:
                    parent_key = graph_key_for_nr[(level - 1, parent_nr)]
                    node_path = parent_key

                if level == len(dendo) - 1:
                    node_key = nr
                else:
                    i = 0
                    while f"{node_path}_{i}" in graph_key_for_nr.values():
                        i += 1

                    node_key = f"{node_path}_{i}"
                    graph_key_for_nr[(level, nr)] = node_key

                D.add_edge(parent_key, node_key)

        _sum_attrs_in_tree(D)

        return clustering, D


def missings_nodes_as_additional_clusters(clustering: NodeClustering):
    """
    Copy the NodeClustering and add the nodes that were not covered by the original clustering.
    E.g nodes that don't have any im_edges or out_edges
    :param clustering: NodeClustering
    :return: NodeClustering
    """
    nodes_clustered = set(itertools.chain.from_iterable(clustering.communities))
    missings_nodes = set(clustering.graph.nodes) - nodes_clustered
    extended_communities = clustering.communities.copy()
    extended_communities.extend([[n] for n in missings_nodes])

    return NodeClustering(
        extended_communities,
        clustering.graph,
        clustering.method_name,
        clustering.method_parameters,
        clustering.overlap,
    )


def _sum_attrs_in_tree(G):
    ordered_nodes = list(reversed(list(nx.bfs_tree(G, "root").nodes)))

    for attr in ["chars_n", "chars_nowhites", "tokens_n", "tokens_unique"]:
        weights = defaultdict(int)
        for node in ordered_nodes:
            if G.out_degree(node) == 0:
                weights[node] = G.nodes[node][attr]

            G.nodes[node][attr] = weights[node]

            parents = list(G.predecessors(node))
            if parents:
                weights[parents[0]] += weights[node]
