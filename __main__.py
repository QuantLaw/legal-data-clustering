import os
import re

from legal_data_clustering.pipeline.cd_cluster import (
    cd_cluster,
    cd_cluster_prepare,
)
from legal_data_clustering.pipeline.cd_cluster_evolution_graph import (
    cd_cluster_evolution_graph,
    cd_cluster_evolution_graph_prepare,
)
from legal_data_clustering.pipeline.cd_cluster_evolution_inspection import (
    cd_cluster_evolution_inspection,
    cd_cluster_evolution_inspection_prepare,
)
from legal_data_clustering.pipeline.cd_cluster_evolution_mappings import (
    cd_cluster_evolution_mappings,
    cd_cluster_evolution_mappings_prepare,
)
from legal_data_clustering.pipeline.cd_cluster_inspection import (
    cd_cluster_inspection,
    cd_cluster_inspection_prepare,
)
from legal_data_clustering.pipeline.cd_cluster_texts import (
    cd_cluster_texts,
    cd_cluster_texts_prepare,
)
from legal_data_clustering.pipeline.cd_preprocessing import (
    cd_preprocessing,
    cd_preprocessing_prepare,
    get_decision_network,
)
from legal_data_clustering.pipeline.main_parser import get_parser
from legal_data_clustering.utils.config_handling import process_items
from legal_data_clustering.utils.statics import (
    ALL_YEARS,
    DE_CD_CLUSTER_EVOLUTION_INSPECTION_PATH,
    DE_CD_CLUSTER_EVOLUTION_MAPPINGS_PATH,
    DE_CD_CLUSTER_EVOLUTION_PATH,
    DE_CD_CLUSTER_INSPECTION_PATH,
    DE_CD_CLUSTER_PATH,
    DE_CD_CLUSTER_TEXTS_PATH,
    DE_CD_PREPROCESSED_GRAPH_PATH,
    DE_CROSSREFERENCE_GRAPH_PATH,
    DE_DECISIONS_NETWORK,
    DE_REFERENCE_PARSED_PATH,
    DE_REG_CD_CLUSTER_EVOLUTION_INSPECTION_PATH,
    DE_REG_CD_CLUSTER_EVOLUTION_MAPPINGS_PATH,
    DE_REG_CD_CLUSTER_EVOLUTION_PATH,
    DE_REG_CD_CLUSTER_INSPECTION_PATH,
    DE_REG_CD_CLUSTER_PATH,
    DE_REG_CD_CLUSTER_TEXTS_PATH,
    DE_REG_CD_PREPROCESSED_GRAPH_PATH,
    DE_REG_CROSSREFERENCE_GRAPH_PATH,
    DE_REG_REFERENCE_PARSED_PATH,
    DE_REG_SNAPSHOT_MAPPING_EDGELIST_PATH,
    DE_SNAPSHOT_MAPPING_EDGELIST_PATH,
    US_CD_CLUSTER_EVOLUTION_INSPECTION_PATH,
    US_CD_CLUSTER_EVOLUTION_MAPPINGS_PATH,
    US_CD_CLUSTER_EVOLUTION_PATH,
    US_CD_CLUSTER_INSPECTION_PATH,
    US_CD_CLUSTER_PATH,
    US_CD_CLUSTER_TEXTS_PATH,
    US_CD_PREPROCESSED_GRAPH_PATH,
    US_CROSSREFERENCE_GRAPH_PATH,
    US_REFERENCE_PARSED_PATH,
    US_REG_CD_CLUSTER_EVOLUTION_INSPECTION_PATH,
    US_REG_CD_CLUSTER_EVOLUTION_MAPPINGS_PATH,
    US_REG_CD_CLUSTER_EVOLUTION_PATH,
    US_REG_CD_CLUSTER_INSPECTION_PATH,
    US_REG_CD_CLUSTER_PATH,
    US_REG_CD_CLUSTER_TEXTS_PATH,
    US_REG_CD_PREPROCESSED_GRAPH_PATH,
    US_REG_CROSSREFERENCE_GRAPH_PATH,
    US_REG_REFERENCE_PARSED_PATH,
    US_REG_SNAPSHOT_MAPPING_EDGELIST_PATH,
    US_SNAPSHOT_MAPPING_EDGELIST_PATH,
)

if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    steps = [step.lower() for step in args.steps]
    dataset = args.dataset.lower()
    use_multiprocessing = args.use_multiprocessing
    overwrite = args.overwrite
    snapshots = args.snapshots
    regulations = args.regulations
    assert args.seeds > 0
    cluster_mapping_configs = dict(
        pp_ratios=args.pp_ratios,
        pp_decays=args.pp_decays,
        pp_merges=args.pp_merges,
        pp_co_occurrences=args.pp_co_occurrences,
        pp_co_occurrence_types=args.pp_co_occurrence_types,
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
                "E.g. for de --snapshots 2012-01-31 2013-01-31 "
                "or for us --snapshot 2001"
            )

    if "all" in steps:
        steps = [
            "preprocess",
            "cluster",
            "cluster_texts",
            "cluster_evolution_mappings",
            "cluster_evolution_graph",
            "cluster_inspection",
            "cluster_evolution_inspection",
        ]

    if "preprocess" in steps:
        if dataset == "de":
            source_folder = (
                DE_REG_CROSSREFERENCE_GRAPH_PATH
                if regulations
                else DE_CROSSREFERENCE_GRAPH_PATH
            )
            target_folder = (
                DE_REG_CD_PREPROCESSED_GRAPH_PATH
                if regulations
                else DE_CD_PREPROCESSED_GRAPH_PATH
            )
            decision_network_path = DE_DECISIONS_NETWORK
        elif dataset == "us":
            source_folder = (
                US_REG_CROSSREFERENCE_GRAPH_PATH
                if regulations
                else US_CROSSREFERENCE_GRAPH_PATH
            )
            target_folder = (
                US_REG_CD_PREPROCESSED_GRAPH_PATH
                if regulations
                else US_CD_PREPROCESSED_GRAPH_PATH
            )
            decision_network_path = None

        items = cd_preprocessing_prepare(
            overwrite,
            snapshots,
            cluster_mapping_configs,
            source_folder,
            target_folder,
        )

        if (
            dataset == "de"
            and items
            and any(
                v != 0 for v in cluster_mapping_configs["pp_co_occurrences"]
            )
        ):
            get_decision_network(decision_network_path)

        logs = process_items(
            items,
            [],
            action_method=cd_preprocessing,
            use_multiprocessing=use_multiprocessing,
            args=(source_folder, target_folder, decision_network_path),
            processes=4,
        )

    if "cluster" in steps:
        if dataset == "de":
            source_folder = (
                DE_REG_CD_PREPROCESSED_GRAPH_PATH
                if regulations
                else DE_CD_PREPROCESSED_GRAPH_PATH
            )
            target_folder = (
                DE_REG_CD_CLUSTER_PATH if regulations else DE_CD_CLUSTER_PATH
            )
        elif dataset == "us":
            source_folder = (
                US_REG_CD_PREPROCESSED_GRAPH_PATH
                if regulations
                else US_CD_PREPROCESSED_GRAPH_PATH
            )
            target_folder = (
                US_REG_CD_CLUSTER_PATH if regulations else US_CD_CLUSTER_PATH
            )

        items = cd_cluster_prepare(
            overwrite,
            snapshots,
            cluster_mapping_configs,
            source_folder,
            target_folder,
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
            source_folder = (
                DE_REG_CD_CLUSTER_PATH if regulations else DE_CD_CLUSTER_PATH
            )
            target_folder = (
                DE_REG_CD_CLUSTER_TEXTS_PATH
                if regulations
                else DE_CD_CLUSTER_TEXTS_PATH
            )
            reference_parsed_folders = (
                DE_REG_REFERENCE_PARSED_PATH
                if regulations
                else DE_REFERENCE_PARSED_PATH
            )
        elif dataset == "us":
            source_folder = (
                US_REG_CD_CLUSTER_PATH if regulations else US_CD_CLUSTER_PATH
            )
            target_folder = (
                US_REG_CD_CLUSTER_TEXTS_PATH
                if regulations
                else US_CD_CLUSTER_TEXTS_PATH
            )
            reference_parsed_folders = (
                US_REG_REFERENCE_PARSED_PATH
                if regulations
                else US_REFERENCE_PARSED_PATH
            )

        if type(reference_parsed_folders) is str:
            reference_parsed_folders = [reference_parsed_folders]

        items = cd_cluster_texts_prepare(
            overwrite,
            snapshots,
            cluster_mapping_configs,
            source_folder,
            target_folder,
        )
        logs = process_items(
            items,
            [],
            action_method=cd_cluster_texts,
            use_multiprocessing=use_multiprocessing,
            args=(
                dataset,
                source_folder,
                target_folder,
                reference_parsed_folders,
                regulations,
            ),
        )

    if "cluster_evolution_mappings" in steps:

        if dataset == "de":
            source_folder = (
                DE_REG_CROSSREFERENCE_GRAPH_PATH
                if regulations
                else DE_CROSSREFERENCE_GRAPH_PATH
            )
            preprocessed_folder = (
                DE_REG_CD_PREPROCESSED_GRAPH_PATH
                if regulations
                else DE_CD_PREPROCESSED_GRAPH_PATH
            )
            target_folder = (
                DE_REG_CD_CLUSTER_EVOLUTION_MAPPINGS_PATH
                if regulations
                else DE_CD_CLUSTER_EVOLUTION_MAPPINGS_PATH
            )
        elif dataset == "us":
            source_folder = (
                US_REG_CROSSREFERENCE_GRAPH_PATH
                if regulations
                else US_CROSSREFERENCE_GRAPH_PATH
            )
            preprocessed_folder = (
                US_REG_CD_PREPROCESSED_GRAPH_PATH
                if regulations
                else US_CD_PREPROCESSED_GRAPH_PATH
            )
            target_folder = (
                US_REG_CD_CLUSTER_EVOLUTION_MAPPINGS_PATH
                if regulations
                else US_CD_CLUSTER_EVOLUTION_MAPPINGS_PATH
            )

        items = cd_cluster_evolution_mappings_prepare(
            overwrite,
            cluster_mapping_configs,
            source_folder,
            target_folder,
        )
        process_items(
            items,
            [],
            action_method=cd_cluster_evolution_mappings,
            use_multiprocessing=use_multiprocessing,
            args=(source_folder, preprocessed_folder, target_folder),
            processes=2,
        )

    if "cluster_evolution_graph" in steps:

        if dataset == "de":
            source_folder = (
                DE_REG_CD_CLUSTER_PATH if regulations else DE_CD_CLUSTER_PATH
            )
            snaphot_mapping_folder = (
                DE_REG_SNAPSHOT_MAPPING_EDGELIST_PATH
                if regulations
                else DE_SNAPSHOT_MAPPING_EDGELIST_PATH
            ) + "/subseqitems"
            subseqitem_mapping_folder = (
                DE_REG_CD_CLUSTER_EVOLUTION_MAPPINGS_PATH
                if regulations
                else DE_CD_CLUSTER_EVOLUTION_MAPPINGS_PATH
            )
            target_folder = (
                DE_REG_CD_CLUSTER_EVOLUTION_PATH
                if regulations
                else DE_CD_CLUSTER_EVOLUTION_PATH
            )
        elif dataset == "us":
            source_folder = (
                US_REG_CD_CLUSTER_PATH if regulations else US_CD_CLUSTER_PATH
            )
            snaphot_mapping_folder = (
                US_REG_SNAPSHOT_MAPPING_EDGELIST_PATH
                if regulations
                else US_SNAPSHOT_MAPPING_EDGELIST_PATH
            ) + "/subseqitems"
            subseqitem_mapping_folder = (
                US_REG_CD_CLUSTER_EVOLUTION_MAPPINGS_PATH
                if regulations
                else US_CD_CLUSTER_EVOLUTION_MAPPINGS_PATH
            )
            target_folder = (
                US_REG_CD_CLUSTER_EVOLUTION_PATH
                if regulations
                else US_CD_CLUSTER_EVOLUTION_PATH
            )

        items = cd_cluster_evolution_graph_prepare(
            overwrite,
            cluster_mapping_configs,
            source_folder,
            snaphot_mapping_folder,
            subseqitem_mapping_folder,
            target_folder,
        )
        process_items(
            items,
            [],
            action_method=cd_cluster_evolution_graph,
            use_multiprocessing=use_multiprocessing,
            args=(
                source_folder,
                snaphot_mapping_folder,
                subseqitem_mapping_folder,
                target_folder,
                dataset,
            ),
        )

    if "cluster_inspection" in steps:
        if dataset == "de":
            source_folder = (
                DE_REG_CD_CLUSTER_PATH if regulations else DE_CD_CLUSTER_PATH
            )
            target_folder = (
                DE_REG_CD_CLUSTER_INSPECTION_PATH
                if regulations
                else DE_CD_CLUSTER_INSPECTION_PATH
            )
        elif dataset == "us":
            source_folder = (
                US_REG_CD_CLUSTER_PATH if regulations else US_CD_CLUSTER_PATH
            )
            target_folder = (
                US_REG_CD_CLUSTER_INSPECTION_PATH
                if regulations
                else US_CD_CLUSTER_INSPECTION_PATH
            )

        items = cd_cluster_inspection_prepare(
            overwrite,
            snapshots,
            cluster_mapping_configs,
            source_folder,
            target_folder,
        )
        logs = process_items(
            items,
            [],
            action_method=cd_cluster_inspection,
            use_multiprocessing=use_multiprocessing,
            args=(dataset, source_folder, target_folder, regulations),
        )

    if "cluster_evolution_inspection" in steps:
        if dataset == "de":
            source_folder = (
                DE_REG_CD_CLUSTER_EVOLUTION_PATH
                if regulations
                else DE_CD_CLUSTER_EVOLUTION_PATH
            )
            crossreference_graph_folder = os.path.join(
                DE_REG_CROSSREFERENCE_GRAPH_PATH
                if regulations
                else DE_CROSSREFERENCE_GRAPH_PATH,
                "seqitems",
            )
            target_folder = (
                DE_REG_CD_CLUSTER_EVOLUTION_INSPECTION_PATH
                if regulations
                else DE_CD_CLUSTER_EVOLUTION_INSPECTION_PATH
            )
        elif dataset == "us":
            source_folder = (
                US_REG_CD_CLUSTER_EVOLUTION_PATH
                if regulations
                else US_CD_CLUSTER_EVOLUTION_PATH
            )
            crossreference_graph_folder = os.path.join(
                US_REG_CROSSREFERENCE_GRAPH_PATH
                if regulations
                else US_CROSSREFERENCE_GRAPH_PATH,
                "seqitems",
            )
            target_folder = (
                US_REG_CD_CLUSTER_EVOLUTION_INSPECTION_PATH
                if regulations
                else US_CD_CLUSTER_EVOLUTION_INSPECTION_PATH
            )

        items = cd_cluster_evolution_inspection_prepare(
            overwrite,
            cluster_mapping_configs,
            source_folder,
            crossreference_graph_folder,
            target_folder,
        )
        logs = process_items(
            items,
            [],
            action_method=cd_cluster_evolution_inspection,
            use_multiprocessing=use_multiprocessing,
            args=(dataset, source_folder, target_folder),
        )
        global cd_cluster_evolution_inspection_graphs
        cd_cluster_evolution_inspection_graphs = None
