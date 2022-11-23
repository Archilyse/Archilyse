from setuptools import find_packages, setup

setup(
    name="common_utils",
    version="1.0.0",
    packages=find_packages(".", exclude=["tests", "scripts"]),
)
