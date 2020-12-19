import os

import networkx as nx

from legal_data_clustering.utils.config_handling import get_configs
from legal_data_clustering.utils.config_parsing import filename_for_pp_config
from legal_data_clustering.utils.graph_api import (
    cluster_families,
    get_heading_path,
)
from quantlaw.utils.files import ensure_exists, list_dir
from quantlaw.utils.networkx import hierarchy_graph

source_file_ext = ".json"


def cd_cluster_evolution_inspection_prepare(
    overwrite,
    cluster_mapping_configs,
    source_folder,
    crossreference_graph_folder,
    target_folder,
):
    ensure_exists(target_folder)

    configs = get_configs(cluster_mapping_configs)

    existing_files = set(list_dir(target_folder, ".htm"))
    if not overwrite:
        configs = [
            config
            for config in configs
            if filename_for_pp_config(
                snapshot="all", **config, file_ext=".htm"
            )
            not in existing_files
        ]
    global cd_cluster_evolution_inspection_graphs
    cd_cluster_evolution_inspection_graphs = {
        f[: -len(".gpickle.gz")]: hierarchy_graph(
            nx.read_gpickle(os.path.join(crossreference_graph_folder, f))
        )
        for f in list_dir(crossreference_graph_folder, ".gpickle.gz")
    }

    return configs


def cd_cluster_evolution_inspection(
    config, dataset, source_folder, target_folder
):
    global cd_cluster_evolution_inspection_graphs
    source_filename_base = filename_for_pp_config(
        snapshot="all", **config, file_ext=""
    )

    G = nx.read_gpickle(
        os.path.join(source_folder, source_filename_base + ".gpickle.gz")
    )
    families = cluster_families(G, 0.15)

    toc = "<h1>TOC</h1><table><th>Index</th><th>Leading cluster</th>\n"
    for idx, family_nodes in enumerate(families[:100]):
        toc += f'<tr><td><a href="#idx_{idx}">Family {idx}</a></td><td> – <a href="#leading_{family_nodes[0]}">{family_nodes[0]}</a></td></li>\n'
    toc += "</table>\n\n"

    content = "<h1>Content</h1>"
    for idx, family_nodes in enumerate(families[:100]):
        content += f'<h2><a name="idx_{idx}"></a><a href="#top">Family {idx} – {family_nodes[0]}</a></h2>\n'
        content += '<div style="padding: 0 40px">'

        family_nodes_sorted = sorted(
            family_nodes,
            key=lambda x: (x.split("_")[0], family_nodes.index(x)),
        )

        content += "<i>"
        for idx, cluster in enumerate(family_nodes_sorted):
            if idx:
                content += " | "
            content += f'<a href="#leading_{cluster}">{cluster}</a>'
        content += "</i>"
        last_year = None
        for cluster in family_nodes_sorted:
            year = cluster.split("_")[0]
            if last_year is not None and last_year != year:
                content += "<hr>"
            content += f'<h3><a name="leading_{cluster}"></a><a href="#top">{cluster}</a></h3>\n'
            if cluster == family_nodes[0]:
                content += f"<i>LEADING</i>"
            content += "<table>"
            cluster_tokens_n = G.nodes[cluster]["tokens_n"]
            for node in G.nodes[cluster]["nodes_contained"].split(","):

                G_hierarchy = cd_cluster_evolution_inspection_graphs[year]
                content += (
                    '<tr><td style="text-align: right; padding-right: 2em;">'
                    + f'{G_hierarchy.nodes[node]["tokens_n"]/cluster_tokens_n*100:.2f} %</td><td>'
                    + G_hierarchy.nodes[node].get('document_type', '')
                    + '</td><td>'
                    + get_heading_path(G_hierarchy, node)
                    + "</td></tr>"
                )
            content += "</table>"

            last_year = year

        content += "</div><hr>"
    with open(f"{target_folder}/{source_filename_base}.htm", "w") as f:
        f.write(
            """<!DOCTYPE html>
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
            <a name="top"></a>
        """
        )
        f.write(toc)
        f.write(content)
        f.write("</body></html>")
