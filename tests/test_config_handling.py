from legal_data_clustering.utils.config_handling import \
    simplify_config_for_preprocessed_graph
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
