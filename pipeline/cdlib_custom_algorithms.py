import itertools

import infomap as imp
from cdlib import NodeClustering
from cdlib.utils import convert_graph_formats
import networkx as nx
from collections import defaultdict


def infomap(
    g,
    seed=None,
    options="--inner-parallelization --silent",
    markov_time=1.0,
    number_of_modules=None,
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
    return NodeClustering(
        coms_infomap, g, "Infomap", method_parameters={"options": options, "seed": seed}
    )


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
