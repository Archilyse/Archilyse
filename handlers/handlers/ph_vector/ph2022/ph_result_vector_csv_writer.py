import csv
from csv import DictReader, DictWriter
from dataclasses import asdict, fields
from pathlib import Path
from typing import Dict, List

from common_utils.constants import RESULT_VECTORS

from . import AreaVectorSchema


class PHResultVectorCSVWriter:
    DELIMITER = ","

    @classmethod
    def write_to_csv(
        cls,
        vectors: Dict[RESULT_VECTORS, List],
        directory: Path,
        schema=AreaVectorSchema,
    ):
        for result_vector_type, result_vector in vectors.items():
            filename = directory.joinpath(result_vector_type.value).with_suffix(".csv")
            with open(filename, mode="w") as f:
                writer = DictWriter(
                    f,
                    delimiter=cls.DELIMITER,
                    quoting=csv.QUOTE_MINIMAL,
                    quotechar='"',
                    fieldnames=sorted(field.name for field in fields(schema)),
                )
                writer.writeheader()
                writer.writerows(asdict(row) for row in result_vector)

    @classmethod
    def read_from_csv(
        cls,
        result_vector_type: RESULT_VECTORS,
        directory: Path,
        schema=AreaVectorSchema,
    ):
        filename = directory.joinpath(result_vector_type.value).with_suffix(".csv")

        vector = []
        with open(filename, mode="r") as f:
            reader = DictReader(
                f,
                delimiter=cls.DELIMITER,
                quoting=csv.QUOTE_MINIMAL,
                quotechar='"',
                fieldnames=sorted(field.name for field in fields(schema)),
            )
            next(reader, None)
            for row in reader:
                vector.append(schema(**row))

        return vector
