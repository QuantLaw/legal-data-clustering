from legal_data_clustering.utils.config_handling import \
    get_configs_for_snapshots
from legal_data_clustering.utils.config_parsing import filename_for_pp_config
from legal_data_clustering.utils.graph_api import (get_clustering_result,
                                                   get_heading_path,
                                                   hierarchy_graph)
from quantlaw.utils.files import ensure_exists, list_dir

source_file_ext = ".json"


def cd_cluster_inspection_prepare(
    overwrite, snapshots, meta_config, source_folder, target_folder
):
    ensure_exists(target_folder)
    items = get_configs_for_snapshots(snapshots, meta_config)

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
        existing_files = list_dir(target_folder, ".htm")
        items = [
            item
            for item in items
            if filename_for_pp_config(**item, file_ext=".htm") not in existing_files
        ]

    return items


def cd_cluster_inspection(
    config,
    dataset,
    source_folder,
    target_folder,
):
    source_filename_base = filename_for_pp_config(**config, file_ext="")

    clustering = get_clustering_result(
        f"{source_folder}/{source_filename_base}{source_file_ext}",
        dataset,
        graph_type="seqitems",
    )

    content = """<!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8"/>
        <style>
        td {
            vertical-align:top;
        }
        body {
            white-space: nowrap;
            font-family: Arial, Helvetica, sans-serif;
        }
        </style>
        </head>
        <body>
    """

    community_tokens_n = [
        sum(clustering.graph.nodes[n]["tokens_n"] for n in nodes)
        for nodes in clustering.communities
    ]

    G_hierarchy = hierarchy_graph(clustering.graph)

    corpus_tokens_n = sum(community_tokens_n)

    for idx_by_size, (community_id, tokens_n) in enumerate(
        sorted(enumerate(community_tokens_n), key=lambda x: -x[-1])
    ):
        content += f"<h3>{idx_by_size+1} | Community {community_id} | {tokens_n} Tokens | {tokens_n/corpus_tokens_n*100:.1f} %</h3>"
        content += "<table><th>Tokens [%]</th><th>Heading path</th>"
        data = sorted(
            [
                (
                    clustering.graph.nodes[n]["tokens_n"],
                    get_heading_path(G_hierarchy, n),
                )
                for n in clustering.communities[community_id]
            ],
            key=lambda x: -x[0],
        )
        for node_tokens_n, heading_path in data:
            node_tokens_n_quotient = (
                f"{node_tokens_n/tokens_n*100:.2f}" if tokens_n else "-"
            )
            content += f'<tr><td style="text-align: right; padding-right: 2em">{node_tokens_n_quotient}</td><td>{heading_path}</td></tr>'
        content += "</table>"
    content += "</body></html>"

    with open(f"{target_folder}/{source_filename_base}.htm", "w") as f:
        f.write(content)
