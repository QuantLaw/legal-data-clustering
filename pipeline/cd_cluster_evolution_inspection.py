import os

import networkx as nx

from legal_data_preprocessing.utils.common import ensure_exists, list_dir
from legal_data_preprocessing.utils.graph_api import hierarchy_graph
from clustering_utils.graph_api import (
    get_clustering_result,
    cluster_families,
    get_heading_path,
)
from clustering_utils.utils import filename_for_pp_config

source_file_ext = ".json"


def cd_cluster_evolution_inspection_prepare(
    overwrite,
    cluster_mapping_configs,
    source_folder,
    crossreference_graph_folder,
    target_folder,
):
    ensure_exists(target_folder)

    # get configs
    configs = [
        dict(
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
        for pp_ratio in cluster_mapping_configs["pp_ratios"]
        for pp_decay in cluster_mapping_configs["pp_decays"]
        for pp_merge in cluster_mapping_configs["pp_merges"]
        for pp_co_occurrence in cluster_mapping_configs["pp_co_occurrences"]
        for pp_co_occurrence_type in cluster_mapping_configs["pp_co_occurrence_types"]
        for markov_time in cluster_mapping_configs["markov_times"]
        for consensus in cluster_mapping_configs["consensus"]
        for seed in cluster_mapping_configs["seeds"]
        for number_of_modules in cluster_mapping_configs["numbers_of_modules"]
        for method in cluster_mapping_configs["methods"]
    ]

    existing_files = set(list_dir(target_folder, ".gpickle.gz"))
    if not overwrite:
        configs = [
            config
            for config in configs
            if filename_for_pp_config(snapshot="all", **config, file_ext=".gpickle.gz")
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


def cd_cluster_evolution_inspection(config, dataset, source_folder, target_folder):
    global cd_cluster_evolution_inspection_graphs
    source_filename_base = filename_for_pp_config(snapshot="all", **config, file_ext="")

    G = nx.read_gpickle(
        os.path.join(source_folder, source_filename_base + ".gpickle.gz")
    )
    families = cluster_families(G, 0.15)

    toc = "<h1>TOC</h1><table><th>Index</th><th>Leading cluster</th>\n"
    for idx, family_nodes in enumerate(families[:20]):
        toc += f'<tr><td><a href="#idx_{1}">Family {idx}</a></td><td> – <a href="#leading_{family_nodes[0]}">{family_nodes[0]}</a></td></li>\n'
    toc += "</table>\n\n"

    content = "<h1>Content</h1>"
    for idx, family_nodes in enumerate(families[:20]):
        content += f'<h2><a name="idx_{idx}"></a><a href="#top">Family {idx} – {family_nodes[0]}</a></h2>\n'
        content += '<div style="padding: 0 40px">'

        family_nodes_sorted = sorted(
            family_nodes, key=lambda x: (x.split("_")[0], family_nodes.index(x))
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
