#####################
# Community detection
#####################


def filename_for_pp_config(
    snapshot,
    pp_ratio,
    pp_decay,
    pp_merge,
    pp_co_occurrence,
    pp_co_occurrence_type,
    file_ext,
    seed=None,
    markov_time=None,
    consensus=0,
    number_of_modules=None,
    method=None,
):
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


def get_config_from_filename(filename):
    components = filename.split("_")
    config = dict(
        snaphot=components[0],
        pp_ratio=float(components[1].replace("-", ".")),
        pp_decay=float(components[2].replace("-", ".")),
        pp_merge=int(components[3].replace("-", ".")),
    )
    if len(components) > 4:
        for component in components[4:]:
            if component.startswith("o"):
                config["pp_co_occurrence"] = float(component[1:].replace("-", "."))
            if component.startswith("t-"):
                config["pp_co_occurrence_type"] = component[len("t-") :]
            if component.startswith("a-"):
                config["method"] = component[len("a-") :]
            if component.startswith("n"):
                config["number_of_modules"] = int(component[1:].replace("-", "."))
            if component.startswith("m"):
                config["markov_time"] = float(component[1:].replace("-", "."))
            if component.startswith("s"):
                config["seed"] = int(component[1:].replace("-", "."))
            if component.startswith("c"):
                config["consensus"] = int(component[1:].replace("-", "."))
    return config
