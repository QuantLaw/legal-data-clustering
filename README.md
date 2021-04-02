[![codecov](https://codecov.io/gh/QuantLaw/legal-data-clustering/branch/master/graph/badge.svg?token=COBPQNeZA7)](https://codecov.io/gh/QuantLaw/legal-data-clustering)
[![Tests](https://github.com/QuantLaw/legal-data-clustering/workflows/Tests/badge.svg)](https://github.com/QuantLaw/legal-data-clustering/actions)
[![Maintainability](https://api.codeclimate.com/v1/badges/a2208e96f66902047627/maintainability)](https://codeclimate.com/repos/5f1ef1fed7f1df01620111b4/maintainability)
[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.4070774.svg)](https://doi.org/10.5281/zenodo.4070774)

# Legal Data Clustering

This repository contains code to cluster legal network data.
It is, inter alia, used to produce the results reported in the following publications:

- Daniel Martin Katz, Corinna Coupette, Janis Beckedorf, and Dirk Hartung, Complex Societies and the Growth of the Law, *Sci. Rep.* **10** (2020), [https://doi.org/10.1038/s41598-020-73623-x](https://doi.org/10.1038/s41598-020-73623-x)
- Corinna Coupette, Janis Beckedorf, Dirk Hartung, Michael Bommarito, and Daniel Martin Katz, Measuring Law Over Time, to appear (2021)

Related Repositories:
- [Complex Societies and the Growth of the Law](https://github.com/QuantLaw/Complex-Societies-and-Growth) ([Publication Release](https://doi.org/10.5281/zenodo.4070769))
- [Legal Data Preprocessing](https://github.com/QuantLaw/legal-data-preprocessing) ([Latest Publication Release](https://doi.org/10.5281/zenodo.4070772))

Related Data: 
- [Preprocessed Input Data for *Sci. Rep.* **10** (2020)](https://doi.org/10.5281/zenodo.4070767)
- [Preprocessed Input Data for *Measuring Law Over Time*, to appear (2021)](https://doi.org/10.5281/zenodo.4660133)

## Setup

1. It is assumed that you have Python 3.7 installed. (Other versions are not tested.)
2. Set up a virtual environment and activate it. (This is not required but recommended.)
3. Install the required packages `pip install -r requirements.txt`.


## Usage

### Download or Generate the Data

One option is to generate the required data yourself using
https://github.com/QuantLaw/legal-data-preprocessing (also available
at https://doi.org/10.5281/zenodo.4070772).

Another option is to use the generated data from the related datasets (see above).
This repository also contains the clustering results. To execute the clustering, you
only need the following directories, other directories should be removed as otherwise
clustering steps might be skipped.

Required files for Germany relative to this repository

- `../legal-networks-data/de/2_xml`
- `../legal-networks-data/de/4_crossreference_graph`
- `../legal-networks-data/de/5_snapshot_mapping_edgelist`

Required files for USA relative to this repository

- `../legal-networks-data/us/2_xml`
- `../legal-networks-data/us/4_crossreference_graph`
- `../legal-networks-data/us/5_snapshot_mapping_edgelist`

The combined data of statutes and regulations is located in the `de_reg` and `us_reg` folders next to the `de` and `us` folders.


### Run

Run `./run_example_configs.sh` to preprocess the graphs in multiple
configurations, cluster them, and map the clusterings over all available years.

The following steps will be executed:

1. **Preprocessing** Simplify the graphs so that they can serve as input for
    clustering algorithms.
2. **Cluster** Perform the clustering with infomap or louvain.
3. **Cluster Texts** Collect the text for each cluster. (This step can only be performed
    if the text data is available `../legal-networks-data/{us,de,us_reg,de_reg}/2_xml`.)
4. **Cluster Evolution Mappings** Map the clusters over time.
5. **Cluster Evolution Graph** Create a graph with clusters as nodes and edges indicating
    the dynamics of nodes between snapshots.
6. **Cluster Inspection** Inspect the content of individual clusters.
7. **Cluster Evolution Inspection** Inspect the content of cluster families.
