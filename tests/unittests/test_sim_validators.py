from handlers.sim_validators import UnitsHighSiteViewValidator, UnitsLowSunValidator


def test_units_high_site_view_validator(validation_unit_stats):
    validation = UnitsHighSiteViewValidator(
        units_stats=validation_unit_stats
    ).validate()
    assert validation == {1: UnitsHighSiteViewValidator.msg}


def test_units_low_sun_validator(validation_unit_stats):
    validation = UnitsLowSunValidator(units_stats=validation_unit_stats).validate()
    assert validation == {2: UnitsLowSunValidator.msg}
