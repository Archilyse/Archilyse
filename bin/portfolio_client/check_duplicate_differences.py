"""
Script that determines the duplicates of units based
on the SL index (HNF, ANF, NBR, street) and checks if our models
also have the same basic features.
"""

from pathlib import Path
from typing import Dict, List, Set, Tuple

import pandas as pd
from tqdm import tqdm

from common_utils.constants import ADMIN_SIM_STATUS, OUTPUT_DIR
from common_utils.logger import logger
from handlers.db import ClientDBHandler, QADBHandler, SiteDBHandler, UnitDBHandler

# These columns are used to determine duplicates in a site
QA_COLUMNS = ["HNF", "ANF", "number_of_rooms", "street"]

# These columns should be equal
VECTOR_COLUMNS = [
    "UnitBasics.area-rooms",
    "UnitBasics.area-loggias",
    "UnitBasics.area-kitchens",
    "UnitBasics.area-sunrooms",
    "UnitBasics.area-balconies",
    "UnitBasics.area-bathrooms",
    "UnitBasics.area-corridors",
    "UnitBasics.area-staircases",
    "UnitBasics.area-storage_rooms",
    "UnitBasics.number-of-rooms",
    "UnitBasics.number-of-loggias",
    "UnitBasics.number-of-showers",
    "UnitBasics.number-of-toilets",
    "UnitBasics.number-of-bathtubs",
    "UnitBasics.number-of-kitchens",
    "UnitBasics.number-of-sunrooms",
    "UnitBasics.number-of-balconies",
    "UnitBasics.number-of-bathrooms",
    "UnitBasics.number-of-corridors",
    "UnitBasics.number-of-storage-rooms" "UnitBasics.has-kitchen-window",
]


def _get_duplicate_groups(site_id: int) -> List[Set[str]]:
    qa = QADBHandler.get_by(site_id=site_id)
    unit_data_index = {
        client_id: (data[col] if data[col] else None for col in QA_COLUMNS)
        for client_id, data in qa["data"].items()
    }

    rev_dict = {}
    for key, value in unit_data_index.items():
        rev_dict.setdefault(value, set()).add(key)
    return [values for key, values in rev_dict.items() if len(values) > 1]


def _get_deviating_columns_by_group(site_id: int) -> List[Tuple[Set[str], List[str]]]:
    unit_vectors = {
        data["client_id"]: data["unit_vector_no_balcony"][0]
        for data in UnitDBHandler.find(
            site_id=site_id, output_columns=["client_id", "unit_vector_no_balcony"]
        )
    }

    unit_index_duplicates = _get_duplicate_groups(site_id=site_id)

    deviating_columns: List[Tuple[Set, List[str]]] = []
    for group in unit_index_duplicates:
        group_vectors = pd.concat(
            [
                pd.DataFrame(
                    [[client_id, *unit_vectors[client_id].values()]],
                    columns=["client_id", *unit_vectors[client_id].keys()],
                )
                for client_id in group
            ]
        ).set_index("client_id", drop=True)[VECTOR_COLUMNS]

        # A group has a problem if one of the duplicates deviates
        # by the group mean by more than 5% or, if it's an area
        # field by more, than 5% and more than 1sqm.
        mean_abs_error = (group_vectors - group_vectors.mean()).abs()
        mean_rel_error = (
            group_vectors - group_vectors.mean()
        ).abs() / group_vectors.mean()

        deviating_columns = list()
        for column in mean_rel_error.columns:
            for (_, rel_error), (_, abs_error) in zip(
                mean_rel_error.iterrows(), mean_abs_error.iterrows()
            ):
                if rel_error[column] > 0.05:
                    if "area" in column and abs_error[column] < 1:
                        continue

                    deviating_columns.append(
                        (column, rel_error[column], abs_error[column])
                    )

        deviating_columns.append((group, deviating_columns))

    return deviating_columns


def _get_suspicious_duplicates(client_id: int) -> pd.DataFrame:
    """Returns a pandas dataframe that contains for each group of
    units that appear to be a duplicate in the qa data a list of columns
    that are not identical.
    """

    deviating_columns_per_site_per_group: Dict[int, List[Tuple[Set, List[str]]]] = {}

    sites = SiteDBHandler.find(
        client_id=client["id"],
        full_slam_results=ADMIN_SIM_STATUS.SUCCESS,
        pipeline_and_qa_complete=True,
        output_columns=["id"],
    )
    for site in tqdm(sites):
        site_id = site["id"]

        try:
            deviating_columns_per_site_per_group[
                site_id
            ] = _get_deviating_columns_by_group(site_id=site_id)
        except Exception as e:
            logger.info(f"ERROR in site {site_id}: {e}")  # noqa: T001

    deviations_by_column_set = []
    for site_id, site_problems in deviating_columns_per_site_per_group.items():
        for group, deviations in site_problems:
            if deviations:
                cols = sorted(set([col for col, _, _ in deviations]))
                deviations_by_column_set.append(
                    (site_id, ", ".join(sorted(group)), ", ".join(sorted(cols)))
                )

    return pd.DataFrame(
        deviations_by_column_set, columns=["site_id", "client_ids", "problems"]
    )


client_name = "Portfolio Client"
client = ClientDBHandler.get_by(name=client_name)
_get_suspicious_duplicates(client_id=client["id"]).to_csv(
    Path(OUTPUT_DIR).joinpath(f"{client_name}_suspicious_duplicates.csv")
)
