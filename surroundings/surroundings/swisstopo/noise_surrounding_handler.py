import functools

from shapely.geometry import Point

from common_utils.constants import NOISE_SOURCE_TYPE, NOISE_TIME_TYPE, SWISSTOPO_DIR
from surroundings.base_noise_surrounding_handler import BaseNoiseLevelHandler
from surroundings.raster_window import RasterioRasterWindow
from surroundings.utils import download_swisstopo_if_not_exists


class SwissTopoNoiseLevelHandler(BaseNoiseLevelHandler):
    NOISE_DATA_FILENAMES = {
        NOISE_SOURCE_TYPE.TRAFFIC: {
            NOISE_TIME_TYPE.DAY: "swisstopo_noise/StrassenLaerm_Tag_LV95.tif",
            NOISE_TIME_TYPE.NIGHT: "swisstopo_noise/StrassenLaerm_Nacht_LV95.tif",
        },
        NOISE_SOURCE_TYPE.TRAIN: {
            NOISE_TIME_TYPE.DAY: "swisstopo_noise/BahnLaerm_Tag_LV95.tif",
            NOISE_TIME_TYPE.NIGHT: "swisstopo_noise/BahnLaerm_Nacht_LV95.tif",
        },
    }

    @functools.cached_property
    def _data_window(self) -> RasterioRasterWindow:
        file_path = self.NOISE_DATA_FILENAMES[self.noise_source_type][
            self.noise_time_type
        ]
        download_swisstopo_if_not_exists(
            bounding_box=self.bounding_box,
            templates=[file_path],
        )
        return RasterioRasterWindow(
            SWISSTOPO_DIR.joinpath(file_path),
            src_bounds=self.bounding_box.bounds,
            fill_nodata=False,
        )

    def get_at(self, location: Point) -> float:
        return self._data_window.get_value_at_xy(x=location.x, y=location.y)
