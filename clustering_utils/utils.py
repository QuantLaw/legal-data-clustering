import multiprocessing


def filename_for_pp_config(
    snapshot,
    pp_ratio,
    pp_decay,
    pp_merge,
    file_ext,
    pp_co_occurrence=None,
    pp_co_occurrence_type=None,
    seed=None,
    markov_time=None,
    consensus=0,
    number_of_modules=None,
    method=None,
):
    if method == "louvain":
        number_of_modules = None

    filename = f"{snapshot}_{pp_ratio}_{pp_decay}_{pp_merge}"
    if pp_co_occurrence:
        filename += f"_o{pp_co_occurrence}_t-{pp_co_occurrence_type}"
    if method:
        filename += f"_a-{method}"
    if number_of_modules:
        filename += f"_n{number_of_modules}"
    if markov_time:
        filename += f"_m{markov_time}"
    if seed is not None:
        filename += f"_s{seed}"
    if consensus:
        filename += f"_c{consensus}"
    return filename.replace(".", "-") + file_ext


def convert_filename_component_to_number(text, value_type=float):
    return value_type(text[0] + text[1:].replace("-", "."))


def get_config_from_filename(filename):
    components = filename.split("_")
    config = dict(
        snapshot=components[0],
        pp_ratio=convert_filename_component_to_number(components[1]),
        pp_decay=convert_filename_component_to_number(components[2]),
        pp_merge=convert_filename_component_to_number(components[3], value_type=int),
    )
    if len(components) > 4:
        for component in components[4:]:
            if component.startswith("o"):
                config["pp_co_occurrence"] = convert_filename_component_to_number(
                    component[1:]
                )
            if component.startswith("t-"):
                config["pp_co_occurrence_type"] = component[len("t-") :]
            if component.startswith("a-"):
                config["method"] = component[len("a-") :]
            if component.startswith("n"):
                config["number_of_modules"] = convert_filename_component_to_number(
                    component[1:], value_type=int
                )
            if component.startswith("m"):
                config["markov_time"] = convert_filename_component_to_number(
                    component[1:]
                )
            if component.startswith("s"):
                config["seed"] = convert_filename_component_to_number(
                    component[1:], value_type=int
                )
            if component.startswith("c"):
                config["consensus"] = convert_filename_component_to_number(
                    component[1:], value_type=int
                )
    return config


def simplify_config_for_preprocessed_graph(config):
    config = config.copy()
    config["seed"] = None
    config["markov_time"] = None
    config["consensus"] = 0
    config["number_of_modules"] = None
    config["method"] = None
    config["file_ext"] = ".gpickle.gz"
    return config


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
