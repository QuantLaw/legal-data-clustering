import os
import re

from lxml import etree
from quantlaw.utils.files import ensure_exists, list_dir

from legal_data_clustering.utils.config_handling import (
    check_for_missing_files,
    get_configs_for_snapshots,
    get_no_overwrite_items,
)
from legal_data_clustering.utils.config_parsing import filename_for_pp_config
from legal_data_clustering.utils.graph_api import get_clustering_result

source_file_ext = ".json"


def cd_cluster_texts_prepare(
    overwrite, snapshots, pp_configs, source_folder, target_folder
):
    ensure_exists(target_folder)
    items = get_configs_for_snapshots(snapshots, pp_configs)

    # Check if source graphs exist
    existing_source_files = set(list_dir(source_folder, source_file_ext))
    required_source_files = {
        filename_for_pp_config(**item, file_ext=source_file_ext)
        for item in items
    }
    check_for_missing_files(
        required_source_files, existing_source_files, "clustering"
    )

    if not overwrite:
        existing_files = os.listdir(target_folder)
        items = get_no_overwrite_items(items, "", existing_files)

    return items


def cd_cluster_texts(
    config,
    dataset,
    source_folder,
    target_folder,
    reference_parsed_folders,
    regulations,
):
    source_filename_base = filename_for_pp_config(**config, file_ext="")

    clustering = get_clustering_result(
        f"{source_folder}/{source_filename_base}{source_file_ext}",
        dataset,
        graph_type="clustering",
        regulations=regulations,
    )
    result_path = ensure_exists(f"{target_folder}/{source_filename_base}")

    reference_parsed_files = {
        os.path.splitext(f)[0]: f
        for reference_parsed_folder in reference_parsed_folders
        for f in list_dir(reference_parsed_folder, ".xml")
    }
    reference_parsed_files = {
        (
            "_".join(k.split("_")[:2] + k.split("_")[-1:])
            if len(k.split('_')) == 4
            else k
        )
        : f
        for k, f in reference_parsed_files.items()
    }
    assert len([
            file
            for reference_parsed_folder in reference_parsed_folders
            for file in list_dir(reference_parsed_folder, ".xml")
        ]) == len(reference_parsed_files)

    for idx, community_nodes in enumerate(clustering.communities):
        community_text = get_community_text(
            community_nodes, reference_parsed_folders, reference_parsed_files
        )
        write_community_text(result_path, idx, community_text)

remove_cfr_volume = re.compile(r'v\d+_')

def get_community_text(
    community_nodes, reference_parsed_folders, reference_parsed_files
):
    loaded_file_name = None
    loaded_file_tree = None
    community_text = ""
    for node in sorted(community_nodes):
        node_filename = "_".join(node.split("_")[:-1])
        # remove volumes from cfr keys
        if node_filename.startswith('cfr'):
            node_filename = remove_cfr_volume.sub('_', node_filename)

        if loaded_file_name != node_filename:
            community_text += "\n\n\n" + node_filename + "\n\n"


            loaded_file_name = reference_parsed_files[node_filename]

            # try to find the file in a reference_parsed_folder
            for reference_parsed_folder in reference_parsed_folders:
                try:

                    loaded_file_tree = etree.parse(
                        os.path.join(reference_parsed_folder, loaded_file_name)
                    )
                    break
                except OSError:
                    if reference_parsed_folder == reference_parsed_folders[-1]:
                        # Last element
                        raise

        tag_text_generator = get_descendants_texts(
            loaded_file_tree.find(f"//*[@key='{node}']")
        )
        tag_text = ' '.join(tag_text_generator)
        community_text += tag_text + " "
    return community_text


def get_descendants_texts(elem, include_tail=False):
    if elem.text:
        text = elem.text.strip()
        if text:
            yield text
    for child in elem.getchildren():
        yield from get_descendants_texts(child, include_tail=True)
    if include_tail and elem.tail:
        tail = elem.tail.strip()
        if tail:
            yield tail


def write_community_text(text_path, idx, community_text):
    with open(f"{text_path}/community_{idx}.txt", "w") as f:
        f.write(community_text)
