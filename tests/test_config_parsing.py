from legal_data_clustering.utils.config_parsing import (
    convert_filename_component_to_number, filename_for_pp_config,
    get_config_from_filename)
from tests.test_classes import ConfigTest


class TestConfigParsing(ConfigTest):
    def test_filename_for_pp_config(self):
        self.assertEqual(
            filename_for_pp_config(*config_dict_to_list(self.config)),
            self.filename,
        )
        other_config = self.config.copy()
        other_config["method"] = "louvain"
        self.assertEqual(
            filename_for_pp_config(*config_dict_to_list(other_config)),
            self.other_filename,
        )
        for attr in [
            "pp_co_occurrence",
            "method",
            "number_of_modules",
            "markov_time",
            "seed",
            "consensus",
        ]:
            other_config[attr] = None
        self.assertEqual(
            filename_for_pp_config(*config_dict_to_list(other_config)),
            self.simple_filename,
        )

    def test_filename_component_to_number(self):
        number = convert_filename_component_to_number("1-0")
        self.assertEqual(number, 1.0)

    def test_get_config_from_filename(self):
        filename, extension = self.filename.split(".")
        filename2, extension2 = self.simple_filename.split(".")
        config = get_config_from_filename(filename)
        config["file_ext"] = "." + extension
        self.assertEqual(self.config, config)
        config = get_config_from_filename(filename2)
        self.assertEqual(
            dict(
                snapshot="x",
                pp_ratio=1.0,
                pp_decay=2.0,
                pp_merge=3,
            ),
            config,
        )


def config_dict_to_list(config):
    return [
        config[attr]
        for attr in [
            "snapshot",
            "pp_ratio",
            "pp_decay",
            "pp_merge",
            "file_ext",
            "pp_co_occurrence",
            "pp_co_occurrence_type",
            "seed",
            "markov_time",
            "consensus",
            "number_of_modules",
            "method",
        ]
    ]
