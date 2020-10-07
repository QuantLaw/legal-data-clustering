import os

from quantlaw.utils.files import ensure_exists, list_dir
from quantlaw.utils.beautiful_soup import create_soup

from clustering_utils.utils import filename_for_pp_config
from clustering_utils.graph_api import get_clustering_result

source_file_ext = ".json"


def cd_cluster_texts_prepare(
    overwrite, snapshots, pp_configs, source_folder, target_folder
):
    ensure_exists(target_folder)
    items = [
        dict(
            snapshot=snapshot,
            pp_ratio=pp_ratio,
            pp_decay=pp_decay,
            pp_merge=pp_merge,
            pp_co_occurrence=pp_co_occurrence,
            pp_co_occurrence_type=pp_co_occurrence_type,
            seed=seed,
            markov_time=markov_time,
            consensus=consensus,
            number_of_modules=number_of_modules,
            method=method,
        )
        for snapshot in snapshots
        for pp_ratio in pp_configs["pp_ratios"]
        for pp_decay in pp_configs["pp_decays"]
        for pp_merge in pp_configs["pp_merges"]
        for pp_co_occurrence in pp_configs["pp_co_occurrences"]
        for pp_co_occurrence_type in pp_configs["pp_co_occurrence_types"]
        for markov_time in pp_configs["markov_times"]
        for consensus in pp_configs["consensus"]
        for seed in pp_configs["seeds"]
        for number_of_modules in pp_configs["numbers_of_modules"]
        for method in pp_configs["methods"]
    ]

    # Check if source graphs exist
    existing_source_files = set(list_dir(source_folder, source_file_ext))
    required_source_files = {
        filename_for_pp_config(**item, file_ext=source_file_ext) for item in items
    }
    missing_source_files = required_source_files - existing_source_files
    if len(missing_source_files):
        raise Exception(
            f'Source clusterings are missing: {" ".join(sorted(missing_source_files))}'
        )

    if not overwrite:
        existing_files = os.listdir(target_folder)
        items = [
            item
            for item in items
            if filename_for_pp_config(**item, file_ext="") not in existing_files
        ]

    return items


def cd_cluster_texts(
    config, dataset, source_folder, target_folder, reference_parsed_folder
):
    source_filename_base = filename_for_pp_config(**config, file_ext="")

    clustering = get_clustering_result(
        f"{source_folder}/{source_filename_base}{source_file_ext}",
        dataset,
        graph_type="clustering",
    )
    result_path = ensure_exists(f"{target_folder}/{source_filename_base}")


    reference_parsed_files = {
        '_'.join(f.split('_')[:2] + os.path.splitext(f)[0].split('_')[-1:]):
        f
        for f in list_dir(reference_parsed_folder, '.xml')
    }
    assert len(list_dir(reference_parsed_folder, '.xml')) == len(reference_parsed_files)

    for idx, community_nodes in enumerate(clustering.communities):
        community_text = get_community_text(community_nodes, reference_parsed_folder, reference_parsed_files)
        write_community_text(result_path, idx, community_text)


def get_community_text(community_nodes, reference_parsed_folder, reference_parsed_files):
    loaded_file_name = None
    loaded_file_soup = None
    community_text = ""
    for node in sorted(community_nodes):
        node_filename = "_".join(node.split("_")[:-1])
        if loaded_file_name != node_filename:
            community_text += "\n\n\n" + node_filename + "\n\n"
            loaded_file_name = reference_parsed_files[node_filename]
            loaded_file_soup = create_soup(os.path.join(reference_parsed_folder, loaded_file_name))

        tag_text = loaded_file_soup.find(key=node).get_text(" ")
        community_text += tag_text + " "
    return community_text


def write_community_text(text_path, idx, community_text):
    with open(f"{text_path}/community_{idx}.txt", "w") as f:
        f.write(community_text)
