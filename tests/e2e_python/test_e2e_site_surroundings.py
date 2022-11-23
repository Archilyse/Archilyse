import os

from common_utils.constants import SurroundingType
from handlers import SiteHandler
from surroundings.surrounding_handler import SurroundingStorageHandler


def test_read_triangles_from_surrounding_file(recreate_test_gcp_bucket, site):
    surroundings = [
        (SurroundingType.LAKES, [(0.0, 0.0, 10.0), (1.0, 1.0, 10.0), (2.0, 2.0, 10.0)])
    ] * 2

    surroundings_path = SiteHandler.get_surroundings_path(
        lv95_location=SiteHandler.get_projected_location(site_info=site)
    )
    SurroundingStorageHandler.upload(
        triangles=surroundings,
        remote_path=surroundings_path,
    )

    # when
    triangles = list(SiteHandler.get_view_surroundings(site_info=site))
    assert not os.path.exists(f"/tmp/{surroundings_path.stem}.csv")
    assert triangles == surroundings
