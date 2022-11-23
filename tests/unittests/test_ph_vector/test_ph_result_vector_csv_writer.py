from csv import DictReader
from dataclasses import asdict, fields
from pathlib import Path
from tempfile import TemporaryDirectory

from common_utils.constants import RESULT_VECTORS
from handlers.ph_vector.ph2022 import AreaVectorSchema, PHResultVectorCSVWriter


class TestPHResultVectorCSVWriter:
    def test_write_to_csv(self):
        result_vector = [
            AreaVectorSchema(
                **{field.name: "1.0" for field in fields(AreaVectorSchema)}
            )
        ]

        vectors = {RESULT_VECTORS.ROOM_VECTOR_WITH_BALCONY: result_vector}

        with TemporaryDirectory() as tempdir:
            directory = Path(tempdir)
            PHResultVectorCSVWriter.write_to_csv(vectors=vectors, directory=directory)

            expected_files = [
                directory.joinpath(
                    RESULT_VECTORS.ROOM_VECTOR_WITH_BALCONY.value
                ).with_suffix(".csv")
            ]

            assert list(directory.iterdir()) == expected_files

            for file in expected_files:
                with open(file) as f:
                    assert list(DictReader(f)) == list(map(asdict, result_vector))

    def test_write_to_csv_adds_headers_if_vector_is_empty(self):
        vectors = {RESULT_VECTORS.ROOM_VECTOR_WITH_BALCONY: []}

        with TemporaryDirectory() as tempdir:
            directory = Path(tempdir)
            PHResultVectorCSVWriter.write_to_csv(vectors=vectors, directory=directory)

            filename = directory.joinpath(
                RESULT_VECTORS.ROOM_VECTOR_WITH_BALCONY.value
            ).with_suffix(".csv")

            with open(filename) as f:
                assert DictReader(f).fieldnames == sorted(
                    field.name for field in fields(AreaVectorSchema)
                )
