from setuptools import find_packages, setup

setup(
    name="celery_tasks",
    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version="1.0.0",
    include_package_data=True,
    packages=find_packages(exclude=["docs", "tests*"]),
)
