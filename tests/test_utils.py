import unittest


from clustering_utils.utils import filename_for_pp_config

class TestUtils(unittest.TestCase):
    def setUp(self):
        self.config = dict(
            snapshot="x",
            pp_ratio=1,
            pp_decay=2,
            pp_merge=3,
            file_ext=".json",
            pp_co_occurrence="a",
            pp_co_occurrence_type="b",
            seed=1234,
            markov_time=1,
            consensus=1000,
            number_of_modules=100,
            method="awesome",
        )

    def test_filename_for_pp_config(self):
        self.assertEqual(filename_for_pp_config(
            *[self.config[attr] for attr in
              ["snapshot", "pp_ratio", "pp_decay", "pp_merge", "file_ext",
               "pp_co_occurrence", "pp_co_occurrence_type", "seed", "markov_time", "consensus", "number_of_modules", "method"]
              ]
        ), "x_1_2_3_oa_t-b_a-awesome_n100_m1_s1234_c1000.json")
