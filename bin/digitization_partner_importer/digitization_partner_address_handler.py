import re
from pathlib import Path

from pandas import DataFrame, read_excel

from bin.digitization_partner_importer.digitization_partner_importer_constants import (
    INDEX_HEADER_LENGTH,
    SHEET_NAME,
)


class DigitizationPartnerAddressHandler:
    @classmethod
    def excel_split_address(cls, file_name: Path):
        dfs: DataFrame = read_excel(
            file_name.as_posix(), sheet_name=SHEET_NAME, skiprows=INDEX_HEADER_LENGTH
        )
        dfs = dfs.rename(
            columns={
                "Adresse": "address",
            }
        )
        dfs = cls.split_address_into_streetname_and_housenumber(dfs=dfs)
        dfs.to_excel(
            excel_writer=Path(file_name.name + "_address_splitted.xlsx"),
            sheet_name=SHEET_NAME,
            startrow=INDEX_HEADER_LENGTH,
        )

    @classmethod
    def split_address_into_streetname_and_housenumber(cls, dfs: DataFrame) -> DataFrame:
        dfs.insert(
            dfs.columns.get_loc("address") + 1,
            "street",
            dfs["address"].apply(cls.get_streetname_from_address),
        )
        dfs.insert(
            dfs.columns.get_loc("street") + 1,
            "housenumber",
            dfs["address"].apply(cls.get_house_number),
        )
        return dfs

    @classmethod
    def get_streetname_from_address(cls, text: str) -> str:
        text = cls._remove_digit_character_combination(text=text)
        text = re.sub(pattern=r"\d", repl="", string=text)
        text = text.strip("/- ")
        return text

    @staticmethod
    def _remove_digit_character_combination(text: str) -> str:
        """
        to catch housenumbers like 46a
        """
        return re.sub(pattern=r"\d[^\s\d/]", repl="", string=text)

    @staticmethod
    def get_house_number(text: str) -> str:
        to_keep = []
        previous_value = ""
        for value in text:
            if value.isdigit():
                to_keep.append(value)
            elif previous_value.isdigit() and not value.isspace():
                to_keep.append(value)
            previous_value = value
        housenumber = "".join(to_keep)
        return housenumber
