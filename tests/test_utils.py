import unittest
from copy import deepcopy

from clustering_utils.utils import (convert_filename_component_to_number,
                                    filename_for_pp_config,
                                    get_config_from_filename, get_configs,
                                    simplify_config_for_preprocessed_graph)


class TestUtils(unittest.TestCase):
    def setUp(self):
        self.config = dict(
            snapshot="x",
            pp_ratio=1.0,
            pp_decay=2.0,
            pp_merge=3,
            file_ext=".json",
            pp_co_occurrence=4.0,
            pp_co_occurrence_type="5-0",
            seed=1234,
            markov_time=1.0,
            consensus=1000,
            number_of_modules=100,
            method="awesome",
        )
        self.filename = "x_1-0_2-0_3_o4-0_t-5-0_a-awesome_n100_m1-0_s1234_c1000.json"
        self.all_cluster_mapping_configs = [
            self.config,
            dict(
                snapshot="x",
                pp_ratio=1.0,
                pp_decay=2.0,
                pp_merge=4,
                file_ext=".json",
                pp_co_occurrence=4.0,
                pp_co_occurrence_type="5-0",
                seed=1234,
                markov_time=1.0,
                consensus=1000,
                number_of_modules=100,
                method="awesome",
            ),
            dict(
                snapshot="x",
                pp_ratio=1.0,
                pp_decay=2.0,
                pp_merge=3,
                file_ext=".json",
                pp_co_occurrence=4.0,
                pp_co_occurrence_type="5-0",
                seed=9999,
                markov_time=1.0,
                consensus=1000,
                number_of_modules=100,
                method="awesome",
            ),
            dict(
                snapshot="x",
                pp_ratio=1.0,
                pp_decay=2.0,
                pp_merge=4,
                file_ext=".json",
                pp_co_occurrence=4.0,
                pp_co_occurrence_type="5-0",
                seed=9999,
                markov_time=1.0,
                consensus=1000,
                number_of_modules=100,
                method="awesome",
            ),
        ]
        self.cluster_mapping_configs = dict(
            pp_ratios=[1.0],
            pp_decays=[2.0],
            pp_merges=[3, 4],
            pp_co_occurrences=[4.0],
            pp_co_occurrence_types=["5-0"],
            seeds=[1234, 9999],
            markov_times=[1.0],
            consensus=[1000],
            numbers_of_modules=[100],
            methods=["awesome"],
        )

    def test_filename_for_pp_config(self):
        self.assertEqual(
            filename_for_pp_config(
                *[
                    self.config[attr]
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
            ),
            self.filename,
        )

    def test_filename_component_to_number(self):
        number = convert_filename_component_to_number("1-0")
        self.assertEqual(number, 1.0)

    def test_get_config_from_filename(self):
        filename, extension = self.filename.split(".")
        config = get_config_from_filename(filename)
        config["file_ext"] = "." + extension
        self.assertEqual(self.config, config)

    def test_simplify_config_for_preprocessed_graph(self):
        config = simplify_config_for_preprocessed_graph(self.config)
        self.assertEqual(config["seed"], None)
        self.assertEqual(config["markov_time"], None)
        self.assertEqual(config["consensus"], 0)
        self.assertEqual(config["number_of_modules"], None)
        self.assertEqual(config["method"], None)
        self.assertEqual(config["file_ext"], ".gpickle.gz")
        for attr in [
            "snapshot",
            "pp_ratio",
            "pp_decay",
            "pp_merge",
            "pp_co_occurrence",
            "pp_co_occurrence_type",
        ]:
            self.assertEqual(config[attr], self.config[attr])

    def test_get_configs(self):
        configs = get_configs(self.cluster_mapping_configs)
        for config in configs:
            config["file_ext"] = ".json"
            config["snapshot"] = "x"
            self.assertTrue(config in self.all_cluster_mapping_configs)
        for config in self.all_cluster_mapping_configs:
            self.assertTrue(config in configs)
