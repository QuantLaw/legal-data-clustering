import multiprocessing

from legal_data_clustering.utils.config_parsing import filename_for_pp_config


def process_items(
    items,
    selected_items,
    action_method,
    use_multiprocessing,
    args=[],
    chunksize=None,
    processes=None,
    spawn=False,
):
    if len(selected_items) > 0:
        filtered_items = []
        for item in list(items):
            for selected_item in selected_items:
                if selected_item in item:
                    filtered_items.append(item)
                    break
        items = filtered_items
    if not processes:
        processes = int(multiprocessing.cpu_count() - 2)
    if use_multiprocessing and len(items) > 1:
        if spawn:
            ctx = multiprocessing.get_context("spawn")
        else:
            ctx = multiprocessing.get_context()
            # A bit slower, but it reimports everything which is necessary
            # to make matplotlib working.
            # Chunksize should be higher or none.
        with ctx.Pool(processes=processes) as p:
            logs = p.starmap(action_method, [(i, *args) for i in items], chunksize)
    else:
        logs = []
        for item in items:
            logs.append(action_method(item, *args))

    return logs


def get_configs_for_snapshots(snapshots, meta_config):
    return [
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
        for pp_ratio in meta_config["pp_ratios"]
        for pp_decay in meta_config["pp_decays"]
        for pp_merge in meta_config["pp_merges"]
        for pp_co_occurrence in meta_config["pp_co_occurrences"]
        for pp_co_occurrence_type in meta_config["pp_co_occurrence_types"]
        for markov_time in meta_config["markov_times"]
        for consensus in meta_config["consensus"]
        for seed in meta_config["seeds"]
        for number_of_modules in meta_config["numbers_of_modules"]
        for method in meta_config["methods"]
    ]


def get_configs(meta_config):
    configs = get_configs_for_snapshots([None], meta_config)
    for config in configs:
        del config["snapshot"]
    return configs


def get_no_overwrite_items(items, target_file_ext, existing_files):
    return [
        item
        for item in items
        if filename_for_pp_config(**item, file_ext=target_file_ext)
        not in existing_files
    ]


def check_for_missing_files(
    required_source_files, existing_source_files, missing_graph_type
):
    missing_source_files = required_source_files - existing_source_files
    if len(missing_source_files):
        raise Exception(
            f'Source {missing_graph_type} are missing: {" ".join(sorted(missing_source_files))}'
        )


def simplify_config_for_preprocessed_graph(config):
    config = config.copy()
    config["seed"] = None
    config["markov_time"] = None
    config["consensus"] = 0
    config["number_of_modules"] = None
    config["method"] = None
    config["file_ext"] = ".gpickle.gz"
    return config
