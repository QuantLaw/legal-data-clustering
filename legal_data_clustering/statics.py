ALL_YEARS = list(range(1994, 2019))

US_DATA_PATH = "../../legal-networks-data/us"
US_TEMP_DATA_PATH = "temp/us"

US_REFERENCE_PARSED_PATH = f"{US_DATA_PATH}/2_xml"
US_CROSSREFERENCE_GRAPH_PATH = f"{US_DATA_PATH}/4_crossreference_graph"
US_SNAPSHOT_MAPPING_EDGELIST_PATH = f"{US_DATA_PATH}/5_snapshot_mapping_edgelist"

US_CD_PREPROCESSED_GRAPH_PATH = f"{US_DATA_PATH}/10_preprocessed_graph"
US_CD_CLUSTER_PATH = f"{US_DATA_PATH}/11_cluster_results"
US_CD_CLUSTER_TEXTS_PATH = f"{US_DATA_PATH}/12_cluster_texts"
US_CD_CLUSTER_EVOLUTION_MAPPINGS_PATH = (
    f"{US_TEMP_DATA_PATH}/121_cluster_evolution_mappings"
)
US_CD_CLUSTER_EVOLUTION_PATH = f"{US_DATA_PATH}/13_cluster_evolution_graph"
US_CD_CLUSTER_INSPECTION_PATH = f"{US_DATA_PATH}/14_cluster_inspection"
US_CD_CLUSTER_EVOLUTION_INSPECTION_PATH = (
    f"{US_DATA_PATH}/15_cluster_evolution_inspection"
)

DE_DATA_PATH = "../../legal-networks-data/de"
DE_TEMP_DATA_PATH = "temp/de"

DE_REFERENCE_PARSED_PATH = f"{DE_DATA_PATH}/2_xml"
DE_CROSSREFERENCE_GRAPH_PATH = f"{DE_DATA_PATH}/4_crossreference_graph"
DE_SNAPSHOT_MAPPING_EDGELIST_PATH = f"{DE_DATA_PATH}/5_snapshot_mapping_edgelist"

DE_CD_PREPROCESSED_GRAPH_PATH = f"{DE_DATA_PATH}/10_preprocessed_graph"
DE_CD_CLUSTER_PATH = f"{DE_DATA_PATH}/11_cluster_results"
DE_CD_CLUSTER_TEXTS_PATH = f"{DE_DATA_PATH}/12_cluster_texts"
DE_CD_CLUSTER_EVOLUTION_MAPPINGS_PATH = (
    f"{DE_TEMP_DATA_PATH}/121_cluster_evolution_mappings"
)
DE_CD_CLUSTER_EVOLUTION_PATH = f"{DE_DATA_PATH}/13_cluster_evolution_graph"
DE_CD_CLUSTER_INSPECTION_PATH = f"{DE_DATA_PATH}/14_cluster_inspection"
DE_CD_CLUSTER_EVOLUTION_INSPECTION_PATH = (
    f"{DE_DATA_PATH}/15_cluster_evolution_inspection"
)

DE_DECISIONS_DATA_PATH = "../legal-networks-data/de_decisions"
DE_DECISIONS_NETWORK = f"{DE_DECISIONS_DATA_PATH}/2_network.gpickle.gz"
