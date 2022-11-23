from setuptools import find_packages, setup

setup(
    name="brooks",
    version="0.1.1",
    packages=find_packages(".", exclude=["tests", "scripts"]),
    package_data={"brooks": ["data/classifiers/*.pickle"]},
)
