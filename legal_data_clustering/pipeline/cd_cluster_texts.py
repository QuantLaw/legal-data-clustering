import os

from legal_data_clustering.utils.config_handling import (
    check_for_missing_files, get_items, get_no_overwrite_items)
from legal_data_clustering.utils.config_parsing import filename_for_pp_config
from legal_data_clustering.utils.graph_api import get_clustering_result
from quantlaw.utils.beautiful_soup import create_soup
from quantlaw.utils.files import ensure_exists, list_dir

source_file_ext = ".json"


def cd_cluster_texts_prepare(
    overwrite, snapshots, pp_configs, source_folder, target_folder
):
    ensure_exists(target_folder)
    items = get_items(snapshots, pp_configs)

    # Check if source graphs exist
    existing_source_files = set(list_dir(source_folder, source_file_ext))
    required_source_files = {
        filename_for_pp_config(**item, file_ext=source_file_ext) for item in items
    }
    check_for_missing_files(required_source_files, existing_source_files, "clustering")

    if not overwrite:
        existing_files = os.listdir(target_folder)
        items = get_no_overwrite_items(items, "", existing_files)

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
        "_".join(f.split("_")[:2] + os.path.splitext(f)[0].split("_")[-1:]): f
        for f in list_dir(reference_parsed_folder, ".xml")
    }
    assert len(list_dir(reference_parsed_folder, ".xml")) == len(reference_parsed_files)

    for idx, community_nodes in enumerate(clustering.communities):
        community_text = get_community_text(
            community_nodes, reference_parsed_folder, reference_parsed_files
        )
        write_community_text(result_path, idx, community_text)


def get_community_text(
    community_nodes, reference_parsed_folder, reference_parsed_files
):
    loaded_file_name = None
    loaded_file_soup = None
    community_text = ""
    for node in sorted(community_nodes):
        node_filename = "_".join(node.split("_")[:-1])
        if loaded_file_name != node_filename:
            community_text += "\n\n\n" + node_filename + "\n\n"
            loaded_file_name = reference_parsed_files[node_filename]
            loaded_file_soup = create_soup(
                os.path.join(reference_parsed_folder, loaded_file_name)
            )

        tag_text = loaded_file_soup.find(key=node).get_text(" ")
        community_text += tag_text + " "
    return community_text


def write_community_text(text_path, idx, community_text):
    with open(f"{text_path}/community_{idx}.txt", "w") as f:
        f.write(community_text)
