import unittest


class ConfigTest(unittest.TestCase):
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
        self.other_filename = "x_1-0_2-0_3_o4-0_t-5-0_a-louvain_m1-0_s1234_c1000.json"
        self.simple_filename = "x_1-0_2-0_3.json"
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
