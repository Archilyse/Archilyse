import pytest

from brooks.classifications import CLASSIFICATIONS
from brooks.types import AllAreaTypes
from common_utils.constants import REGION
from connectors.db_connector import get_db_session_scope


@pytest.mark.parametrize(
    "enum_db_name, enum_python",
    [
        ("allareatypes", AllAreaTypes),
        ("classifications", CLASSIFICATIONS),
        ("region", REGION),
    ],
)
def test_enum_synced_between_python_and_pgsql(enum_db_name, enum_python):
    with get_db_session_scope() as session:
        db_enum_values = {
            value[0]
            for value in session.execute(
                f"SELECT unnest(enum_range(NULL::{enum_db_name}));"
            )
        }
        python_enum_values = {entry.name for entry in enum_python}
        if enum_python == REGION:
            python_enum_values.discard(REGION.EUROPE.name)
            python_enum_values.discard(REGION.LAT_LON.name)
        assert python_enum_values == db_enum_values
