ALL_YEARS = list(range(1994, 2020))
ALL_YEARS_REG = list(range(1998, 2020))

US_DATA_PATH = "../legal-networks-data/us"
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

DE_DATA_PATH = "../legal-networks-data/de"
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

# Reg
US_REG_DATA_PATH = "../legal-networks-data/us_reg"
US_REG_TEMP_DATA_PATH = "temp/us_reg"

US_REG_REFERENCE_PARSED_PATH = [
    f"{US_REG_DATA_PATH}/2_xml",
    f"{US_DATA_PATH}/2_xml",
]
US_REG_CROSSREFERENCE_GRAPH_PATH = f"{US_REG_DATA_PATH}/4_crossreference_graph"
US_REG_SNAPSHOT_MAPPING_EDGELIST_PATH = (
    f"{US_REG_DATA_PATH}/5_snapshot_mapping_edgelist"
)

US_REG_CD_PREPROCESSED_GRAPH_PATH = f"{US_REG_DATA_PATH}/10_preprocessed_graph"
US_REG_CD_CLUSTER_PATH = f"{US_REG_DATA_PATH}/11_cluster_results"
US_REG_CD_CLUSTER_TEXTS_PATH = f"{US_REG_DATA_PATH}/12_cluster_texts"
US_REG_CD_CLUSTER_EVOLUTION_MAPPINGS_PATH = (
    f"{US_REG_TEMP_DATA_PATH}/121_cluster_evolution_mappings"
)
US_REG_CD_CLUSTER_EVOLUTION_PATH = f"{US_REG_DATA_PATH}/13_cluster_evolution_graph"
US_REG_CD_CLUSTER_INSPECTION_PATH = f"{US_REG_DATA_PATH}/14_cluster_inspection"
US_REG_CD_CLUSTER_EVOLUTION_INSPECTION_PATH = (
    f"{US_REG_DATA_PATH}/15_cluster_evolution_inspection"
)

DE_REG_DATA_PATH = "../legal-networks-data/de_reg"
DE_REG_TEMP_DATA_PATH = "temp/de_reg"

DE_REG_REFERENCE_PARSED_PATH = f"{DE_REG_DATA_PATH}/2_xml"
DE_REG_CROSSREFERENCE_GRAPH_PATH = f"{DE_REG_DATA_PATH}/4_crossreference_graph"
DE_REG_SNAPSHOT_MAPPING_EDGELIST_PATH = (
    f"{DE_REG_DATA_PATH}/5_snapshot_mapping_edgelist"
)

DE_REG_CD_PREPROCESSED_GRAPH_PATH = f"{DE_REG_DATA_PATH}/10_preprocessed_graph"
DE_REG_CD_CLUSTER_PATH = f"{DE_REG_DATA_PATH}/11_cluster_results"
DE_REG_CD_CLUSTER_TEXTS_PATH = f"{DE_REG_DATA_PATH}/12_cluster_texts"
DE_REG_CD_CLUSTER_EVOLUTION_MAPPINGS_PATH = (
    f"{DE_REG_TEMP_DATA_PATH}/121_cluster_evolution_mappings"
)
DE_REG_CD_CLUSTER_EVOLUTION_PATH = f"{DE_REG_DATA_PATH}/13_cluster_evolution_graph"
DE_REG_CD_CLUSTER_INSPECTION_PATH = f"{DE_REG_DATA_PATH}/14_cluster_inspection"
DE_REG_CD_CLUSTER_EVOLUTION_INSPECTION_PATH = (
    f"{DE_REG_DATA_PATH}/15_cluster_evolution_inspection"
)

DE_DECISIONS_DATA_PATH = "../legal-networks-data/de_decisions"
DE_DECISIONS_NETWORK = f"{DE_DECISIONS_DATA_PATH}/2_network.gpickle.gz"
