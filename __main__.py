import argparse
import re

from legal_data_preprocessing.statics import (
    ALL_YEARS,
    DE_CROSSREFERENCE_GRAPH_PATH,
    US_CROSSREFERENCE_GRAPH_PATH,
    DE_REFERENCE_PARSED_PATH,
    US_REFERENCE_PARSED_PATH,
    DE_SNAPSHOT_MAPPING_EDGELIST_PATH,
    US_SNAPSHOT_MAPPING_EDGELIST_PATH,
)

from pipeline.cd_cluster import cd_cluster_prepare, cd_cluster
from pipeline.cd_cluster_evolution_graph import (
    cd_cluster_evolution_graph_prepare,
    cd_cluster_evolution_graph,
)
from pipeline.cd_cluster_texts import cd_cluster_texts_prepare, cd_cluster_texts
from pipeline.cd_preprocessing import cd_preprocessing_prepare, cd_preprocessing

from legal_data_preprocessing.utils.common import process_items
from statics import (
    DE_CD_PREPROCESSED_GRAPH_PATH,
    US_CD_PREPROCESSED_GRAPH_PATH,
    DE_CD_CLUSTER_PATH,
    US_CD_CLUSTER_PATH,
    DE_CD_CLUSTER_TEXTS_PATH,
    US_CD_CLUSTER_TEXTS_PATH,
    DE_CD_CLUSTER_MAPPED_PATH,
    US_CD_CLUSTER_MAPPED_PATH,
)

if __name__ == "__main__":
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
            "snapshots for crossreferences. Eg. 2010-01-01 for de dataset or 2010 for us dataset. "
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
            "Graph preprocessing parameter. Determines the weight of the highest possible sequence weight. "
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
            "Expressed as negative exponent of the distance of sequential nodes in the hierarchy - 1. "
        ),
    )
    parser.add_argument(
        "--pp-merge",
        dest="pp_merges",
        nargs="+",
        type=int,
        default=[-1],
        help=(
            "Graph preprocessing parameter. The maximal size of parent nodes children are rolled up to. "
            "Only if the size of the parent node remains below the merge (threshold), "
            'its children will be "merged" into the parent. '
            "Special param: -1. Merging into chapter in US and Buch or Gesetz in DE"
        ),
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
        default=[1000],
        help="Rerun infomap with different seeds and altered weights of edges and negotiate common result.",
    )

    parser.add_argument(
        "--number-of-modules",
        dest="numbers_of_modules",
        nargs="+",
        type=int,
        default=[100],
        help="Sets infomap parameter referred-number-of-modules. Default: 100",
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

    args = parser.parse_args()

    steps = [step.lower() for step in args.steps]
    dataset = args.dataset.lower()
    use_multiprocessing = args.use_multiprocessing
    overwrite = args.overwrite
    snapshots = args.snapshots
    assert args.seeds > 0
    cluster_mapping_configs = dict(
        pp_ratios=args.pp_ratios,
        pp_decays=args.pp_decays,
        pp_merges=args.pp_merges,
        seeds=list(range(args.seeds)),
        markov_times=args.markov_times,
        numbers_of_modules=args.numbers_of_modules,
        consensus=args.consensus,
        methods=args.clustering_method,
    )

    if dataset not in ["de", "us"]:
        raise Exception(f"{dataset} unsupported dataset. Options: us, de")

    if "all" in snapshots:
        if dataset == "us":
            snapshots = [f"{year}" for year in ALL_YEARS]
        elif dataset == "de":
            snapshots = [f"{year}-01-01" for year in ALL_YEARS]

    # Validate snapshot format
    for snapshot in snapshots:
        if not re.fullmatch(r"\d{4}(-\d{2}-\d{2})?", snapshot):
            raise Exception(
                "Add --snapshots as argument. "
                "E.g. for de --snapshots 2012-01-31 2013-01-31 or for us --snapshot 2001"
            )

    if "all" in steps:
        steps = [
            "preprocess",
            "cluster",
            "cluster_texts",
            "cluster_evolution_graph",
        ]

    if "preprocess" in steps:
        if dataset == "de":
            source_folder = DE_CROSSREFERENCE_GRAPH_PATH
            target_folder = DE_CD_PREPROCESSED_GRAPH_PATH
        elif dataset == "us":
            source_folder = US_CROSSREFERENCE_GRAPH_PATH
            target_folder = US_CD_PREPROCESSED_GRAPH_PATH

        items = cd_preprocessing_prepare(
            overwrite, snapshots, cluster_mapping_configs, source_folder, target_folder
        )
        logs = process_items(
            items,
            [],
            action_method=cd_preprocessing,
            use_multiprocessing=use_multiprocessing,
            args=(source_folder, target_folder),
        )

    if "cluster" in steps:
        if dataset == "de":
            source_folder = DE_CD_PREPROCESSED_GRAPH_PATH
            target_folder = DE_CD_CLUSTER_PATH
        elif dataset == "us":
            source_folder = US_CD_PREPROCESSED_GRAPH_PATH
            target_folder = US_CD_CLUSTER_PATH

        items = cd_cluster_prepare(
            overwrite, snapshots, cluster_mapping_configs, source_folder, target_folder
        )
        logs = process_items(
            items,
            [],
            action_method=cd_cluster,
            use_multiprocessing=use_multiprocessing,
            args=(source_folder, target_folder),
        )

    if "cluster_texts" in steps:
        if dataset == "de":
            source_folder = DE_CD_CLUSTER_PATH
            target_folder = DE_CD_CLUSTER_TEXTS_PATH
            reference_parsed_folder = DE_REFERENCE_PARSED_PATH
        elif dataset == "us":
            source_folder = US_CD_CLUSTER_PATH
            target_folder = US_CD_CLUSTER_TEXTS_PATH
            reference_parsed_folder = US_REFERENCE_PARSED_PATH

        items = cd_cluster_texts_prepare(
            overwrite, snapshots, cluster_mapping_configs, source_folder, target_folder
        )
        logs = process_items(
            items,
            [],
            action_method=cd_cluster_texts,
            use_multiprocessing=use_multiprocessing,
            args=(dataset, source_folder, target_folder, reference_parsed_folder),
        )

    if "cluster_evolution_graph" in steps:

        if dataset == "de":
            source_folder = DE_CD_CLUSTER_PATH
            mapping_folder = DE_SNAPSHOT_MAPPING_EDGELIST_PATH + "/subseqitems"
            target_folder = DE_CD_CLUSTER_MAPPED_PATH
        elif dataset == "us":
            source_folder = US_CD_CLUSTER_PATH
            mapping_folder = US_SNAPSHOT_MAPPING_EDGELIST_PATH + "/subseqitems"
            target_folder = US_CD_CLUSTER_MAPPED_PATH

        items = cd_cluster_evolution_graph_prepare(
            overwrite,
            cluster_mapping_configs,
            source_folder,
            mapping_folder,
            target_folder,
        )
        logs = process_items(
            items,
            [],
            action_method=cd_cluster_evolution_graph,
            use_multiprocessing=use_multiprocessing,
            args=(source_folder, mapping_folder, target_folder, dataset),
        )