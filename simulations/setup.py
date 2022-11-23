""" Setup to run tox jobs on CI stage """
from setuptools import find_packages, setup

setup(
    name="simulation",
    description="archilyse simulations package",
    version="0.1.63",
    packages=find_packages(".", exclude=["tests", "scripts"]),
)
