from legal_data_clustering.utils.config_handling import (
    get_configs,
    get_configs_for_snapshots,
    simplify_config_for_preprocessed_graph,
)
from tests.test_classes import ConfigTest


class TestConfigHandling(ConfigTest):
    def test_simplify_config_for_preprocessed_graph(self):
        config = simplify_config_for_preprocessed_graph(self.config)
        for attr in ["seed", "markov_time", "number_of_modules", "method"]:
            self.assertEqual(config[attr], None)
        self.assertEqual(config["consensus"], 0)
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

    def test_get_configs_for_snapshots(self):
        configs = get_configs_for_snapshots(["x"], self.cluster_mapping_configs)
        for config in configs:
            config["file_ext"] = ".json"
            self.assertTrue(config in self.all_cluster_mapping_configs)
        for config in self.all_cluster_mapping_configs:
            self.assertTrue(config in configs)

    def test_get_configs(self):
        configs = get_configs(self.cluster_mapping_configs)
        for config in configs:
            config["file_ext"] = ".json"
            config["snapshot"] = "x"
            self.assertTrue(config in self.all_cluster_mapping_configs)
        for config in self.all_cluster_mapping_configs:
            self.assertTrue(config in configs)
