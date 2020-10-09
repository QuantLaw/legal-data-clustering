import argparse


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", help="select a dataset: DE or US")
    parser.add_argument("steps", nargs="+", help="select a step to perform by name")
    parser.add_argument(
        "--single-process",
        dest="use_multiprocessing",
        action="store_const",
        const=False,
        default=True,
        help="prevent multiprocessing",
    )
    parser.add_argument(
        "--overwrite",
        dest="overwrite",
        action="store_const",
        const=True,
        default=False,
        help="overwrite files",
    )
    parser.add_argument(
        "--snapshots",
        dest="snapshots",
        nargs="*",
        type=str,
        default=["all"],
        help=(
            "snapshots for crossreferences."
            "Eg. 2010-01-01 for de dataset or 2010 for us dataset. "
            "To run on whole research window: all"
        ),
    )

    # Preprocessing args
    parser.add_argument(
        "--pp-ratio",
        dest="pp_ratios",
        nargs="+",
        type=float,
        default=[0.0],
        help=(
            "Graph preprocessing parameter. "
            "Determines the weight of the highest possible sequence weight. "
            "If 0, sequences are excluded."
            "The weight of cross-references is constantly 1."
        ),
    )
    parser.add_argument(
        "--pp-decay",
        dest="pp_decays",
        nargs="+",
        type=float,
        default=[1.0],
        help=(
            "Graph preprocessing parameter. Determines how sequence edges decay, "
            "if sequential nodes are not part of the lowest chapter."
            "Expressed as negative exponent of the distance of sequential nodes "
            "in the hierarchy - 1. "
        ),
    )
    parser.add_argument(
        "--pp-merge",
        dest="pp_merges",
        nargs="+",
        type=int,
        default=[-1],
        help=(
            "Graph preprocessing parameter. "
            "The maximal size of parent nodes children are rolled up to. "
            "Only if the size of the parent node remains below the merge (threshold), "
            "its children will be 'merged' into the parent. "
            "Special param: -1. Merging into chapter in US and Buch or Gesetz in DE"
        ),
    )
    parser.add_argument(
        "--pp-co-occurrence",
        dest="pp_co_occurrences",
        nargs="+",
        type=float,
        default=[0],
        help="Select if you want to add co-occurrences to the model. "
        "0 ignores crossreferences,"
        "Values > 0 set the weight of crossreferences"
        "-1 ignores cross-references and uses co-occurrences only",
    )
    parser.add_argument(
        "--pp-co-occurrence-type",
        dest="pp_co_occurrence_types",
        nargs="+",
        type=str,
        default=[None],
        help="If co-occurrence is not 0, select a type. Options: "
        "document (uses co-occurrences of e.g. a decision)"
        "seqitem (uses co-occurrences of e.g. a paragraph of a decision)",
    )

    # Cluster args
    parser.add_argument(
        "--seed",
        dest="seeds",
        nargs="?",
        type=int,
        default=1,
        help="Number of different seeds. Range starting at 0",
    )
    parser.add_argument(
        "--consensus",
        dest="consensus",
        nargs="+",
        type=int,
        default=[0],
        help="Rerun the clustering with different seeds and altered weights of "
        "edges and negotiate common result.",
    )

    parser.add_argument(
        "--number-of-modules",
        dest="numbers_of_modules",
        nargs="+",
        type=int,
        default=[0],
        help="Sets infomap parameter referred-number-of-modules. "
        "(no effect for louvain) Default: 0",
    )

    parser.add_argument(
        "--markov-time",
        dest="markov_times",
        nargs="+",
        type=float,
        default=[1.0],
        help="Markov time for infomap. Default: 1",
    )

    parser.add_argument(
        "--clustering-method",
        dest="clustering_method",
        nargs="+",
        type=str,
        default=["infomap"],
        help="Choose clustering method. infomap or louvain",
    )
    return parser
