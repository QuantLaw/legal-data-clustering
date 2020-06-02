#####################
# Community detection
#####################


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
