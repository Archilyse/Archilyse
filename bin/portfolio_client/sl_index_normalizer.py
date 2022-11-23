import csv
import pathlib

from handlers.db.qa_handler import INDEX_HNF_AREA, INDEX_NET_AREA, INDEX_ROOM_NUMBER

final_data = []

for csv_file in pathlib.Path("csv_files").glob("*.csv"):
    with csv_file.open("r") as f:
        readCSV = csv.reader(f, delimiter=",")
        header = next(iter(readCSV))
        hnf_idx = header.index("HNF")
        assetmanager_idx = header.index("Mietfläche AssetManager")
        n_rooms_idx = header.index("Anzahl Zimmer")
        room_type_idx = header.index("Art")
        for row in readCSV:
            if "wohnen" not in row[room_type_idx].lower():
                continue

            client_site_id = row[0]
            apartment_client_id = row[4]
            hnf = row[hnf_idx]
            assetmanager = row[assetmanager_idx]
            n_rooms = row[n_rooms_idx]
            final_data.append(
                {
                    "apartment_client_id": apartment_client_id,
                    "Obje": client_site_id,
                    INDEX_HNF_AREA: hnf,
                    INDEX_NET_AREA: assetmanager,
                    INDEX_ROOM_NUMBER: n_rooms,
                }
            )

keys = final_data[0].keys()
with open("final_file.csv", "w") as final_file:
    dict_writer = csv.DictWriter(final_file, keys)
    dict_writer.writeheader()
    dict_writer.writerows(final_data)
