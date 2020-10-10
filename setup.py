from setuptools import find_namespace_packages, setup

setup(
    name="legal_data_clustering",
    version="0.0.1",
    description="Detect communities in legal networks",
    url="git@github.com:QuantLaw/legal-data-clustering.git",
    author="QuantLaw Research Group",
    author_email="",
    license="new-bsd",
    packages=find_namespace_packages(include=["legal_data_clustering.*"]),
    zip_safe=False,
)
