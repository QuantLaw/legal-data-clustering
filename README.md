[![codecov](https://codecov.io/gh/QuantLaw/legal-data-clustering/branch/master/graph/badge.svg?token=COBPQNeZA7)](https://codecov.io/gh/QuantLaw/legal-data-clustering)
[![Tests](https://github.com/QuantLaw/legal-data-clustering/workflows/Tests/badge.svg)](https://github.com/QuantLaw/legal-data-clustering/actions)
[![Maintainability](https://api.codeclimate.com/v1/badges/a2208e96f66902047627/maintainability)](https://codeclimate.com/repos/5f1ef1fed7f1df01620111b4/maintainability)
[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.4070775.svg)](http://dx.doi.org/10.5281/zenodo.4070775)

# Legal Data Clustering

This repository contains code to cluster legal network data.
It is, inter alia, used to produce the results reported in the following publication:

Daniel Martin Katz, Corinna Coupette, Janis Beckedorf, and Dirk Hartung, Complex Societies and the Growth of the Law, *Sci. Rep.* **10** (2020), [https://doi.org/10.1038/s41598-020-73623-x](https://doi.org/10.1038/s41598-020-73623-x)

Related Repositories:
- [Complex Societies and the Growth of the Law](https://github.com/QuantLaw/Complex-Societies-and-Growth) ([First Publication Release](http://dx.doi.org/10.5281/zenodo.4070769))
- [Legal Data Preprocessing](https://github.com/QuantLaw/legal-data-preprocessing) ([First Publication Release](http://dx.doi.org/10.5281/zenodo.4070773))

Related Data: [Preprocessed Input Data for *Sci. Rep.* **10** (2020)](http://dx.doi.org/10.5281/zenodo.4070767)

## Setup

1. It is assumed that you have Python 3.7 installed. (Other versions are not tested.)
2. Set up a virtual environment and activate it. (This is not required but recommended.)
3. Install the required packages `pip install -r requirements.txt`.


## Usage

### Download or generate the data

One option is to generate the required data yourself using
https://github.com/QuantLaw/legal-data-preprocessing (also available
at http://dx.doi.org/10.5281/zenodo.4070773 .)

Another option is to use the generated data from  [Preprocessed Input Data for *Sci. Rep.* **10** (2020)](http://dx.doi.org/10.5281/zenodo.4070767)
This repository also contains the clustering results. To execute the clustering you
only need the following directories. The other directories should be removed as otherwise
clustering steps might be skipped.

Required files for Germany relative to this repository

- ../legal-networks-data/de/2_xml
- ../legal-networks-data/de/4_crossreference_graph
- ../legal-networks-data/de/5_snapshot_mapping_edgelist

Required files for USA relative to this repository

- ../legal-networks-data/us/2_xml
- ../legal-networks-data/us/4_crossreference_graph
- ../legal-networks-data/us/5_snapshot_mapping_edgelist


### Run

Execute `./run_example_configs.sh` to preprocess the graphs in multiple
configurations, cluster them, map the clusterings over all available years.
