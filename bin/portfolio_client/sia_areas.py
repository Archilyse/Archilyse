from pathlib import Path

import pandas as pd
from tqdm import tqdm

from handlers.db import ClientDBHandler, SiteDBHandler, UnitDBHandler

EXPORT_COLUMNS = [
    "UnitBasics.area-sia416-FF",
    "UnitBasics.area-sia416-VF",
    "UnitBasics.area-sia416-ANF",
    "UnitBasics.area-sia416-HNF",
    "UnitBasics.area-sia416-NNF",
]

client = ClientDBHandler.get_by(name="Portfolio Client")
sites = SiteDBHandler.find(client_id=client["id"], full_slam_results="SUCCESS")
site_ids = [site["id"] for site in sites]
units = UnitDBHandler.find_in(
    site_id=site_ids,
    output_columns=["id", "client_id", "unit_vector_with_balcony"],
)

vectors = []
for unit in tqdm(units):
    if unit["unit_vector_with_balcony"]:
        vector = unit["unit_vector_with_balcony"][0]
        vector["client_id"] = unit["client_id"]
        vectors.append(vector)

df = pd.DataFrame(vectors)


def retransform_client_id(client_id_old):
    try:
        property_id_old = int(client_id_old.split(".")[0])
    except Exception:
        return client_id_old

    if property_id_old in mapping.index:
        property_id_new = mapping.loc[property_id_old].values[0]
        return ".".join([str(property_id_new), *client_id_old.split(".")[1:]])
    return client_id_old


def make_client_id(z):
    try:
        return f'{z["objekt"]}.{int(z["gebäude"]):02d}.{int(z["haus"]):02d}.{int(z["mietobjekt"]):04d}'
    except Exception:
        return None


index = pd.read_csv(
    Path.home().joinpath("Downloads/20210111_alleIDs.xlsx - Sheet1.csv").as_posix(),
    skiprows=2,
)

mapping = pd.read_csv(
    Path.home().joinpath("Downloads/segment_transfers_2021_02_02.csv").as_posix()
)[["property_id_old", "property_id_new"]].set_index("property_id_old", drop=1)

data = df[["client_id"] + EXPORT_COLUMNS]
data.columns = [c if c == "client_id" else c.split("-")[-1] for c in data.columns]
data["client_id"] = data["client_id"].apply(retransform_client_id)

index["client_id"] = index[["objekt", "gebäude", "haus", "mietobjekt"]].apply(
    make_client_id, axis=1
)
result = (
    index[
        [
            "client_id",
            "Sum of HNF",
            "Sum of ANF",
            "Sum of NNF",
            "Sum of VF_vermietet",
            "Sum of flaeche_bewi",
        ]
    ]
    .merge(data, on="client_id")
    .drop_duplicates()
)

result.columns = [c.replace("Sum of ", "Index-") for c in result.columns]
result.to_csv(Path.home().joinpath("Downloads/sl_sia416.csv").as_posix(), index=False)
