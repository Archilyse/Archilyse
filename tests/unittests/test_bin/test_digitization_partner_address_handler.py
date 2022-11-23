import pytest

from bin.digitization_partner_importer.digitization_partner_address_handler import (
    DigitizationPartnerAddressHandler,
)


class TestDigitizationPartnerAddressHandler:
    @staticmethod
    @pytest.mark.parametrize(
        "address, expected_streetname",
        [
            ("Lagerstr.5", "Lagerstr."),
            ("Hardturmstrasse 5", "Hardturmstrasse"),
            ("Centralbahnp. 12/Kuecheng. 9", "Centralbahnp. /Kuecheng."),
            ("Bernstrasse 5-7", "Bernstrasse"),
            ("Bernstrasse 5/7", "Bernstrasse"),
            ("Auwiesenstr. 45b", "Auwiesenstr."),
            ("Saint-Francois 1 / Grand Pond", "Saint-Francois  / Grand Pond"),
        ],
    )
    def test_get_streetname(address, expected_streetname):
        assert (
            DigitizationPartnerAddressHandler.get_streetname_from_address(text=address)
            == expected_streetname
        )

    @staticmethod
    @pytest.mark.parametrize(
        "original_streetname, expected_housenumber",
        [
            ("Lagerstr.501", "501"),
            ("Lagerstrasse 50 ", "50"),
            ("Hardturmstrasse 5", "5"),
            ("Centralbahnp. 12/Kuecheng. 9", "12/9"),
            ("Bernstrasse 5-7", "5-7"),
            ("Bernstrasse 5/7", "5/7"),
            ("Auwiesenstr. 45b", "45b"),
            ("Alpenstr./Bellevuerain(hz/Ga)", ""),
        ],
    )
    def test_get_housenumber(original_streetname, expected_housenumber):
        assert (
            DigitizationPartnerAddressHandler.get_house_number(text=original_streetname)
            == expected_housenumber
        )
