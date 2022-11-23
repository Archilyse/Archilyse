import io
import zipfile

import click
import requests
from tqdm import tqdm

from common_utils.constants import GOOGLE_CLOUD_BUCKET, GOOGLE_CLOUD_OSM
from common_utils.logger import logger
from handlers import GCloudStorageHandler
from surroundings.constants import OSM_REGIONS_FILENAMES

GEOFABRIK_PREFIX = "http://download.geofabrik.de/"

gcloud = GCloudStorageHandler()


@click.command()
def main():
    uploaded_regions = []
    for region_folder in tqdm(OSM_REGIONS_FILENAMES.values()):
        gcloud_path = GOOGLE_CLOUD_OSM.joinpath(region_folder)
        if not gcloud.check_prefix_exists(
            bucket_name=GOOGLE_CLOUD_BUCKET, prefix=gcloud_path
        ):
            logger.info(f"Updating region {str(region_folder)}")
            uploaded_regions.append(str(region_folder))
            geofabrik_url = GEOFABRIK_PREFIX + str(region_folder) + ".zip"

            request = requests.get(geofabrik_url)
            with zipfile.ZipFile(file=io.BytesIO(request.content)) as osm_zipped_file:
                for filename in osm_zipped_file.namelist():
                    gcloud.upload_bytes_to_bucket(
                        bucket_name=GOOGLE_CLOUD_BUCKET,
                        destination_folder=gcloud_path,
                        destination_file_name=filename,
                        contents=osm_zipped_file.read(filename),
                    )
    if uploaded_regions:
        logger.info(f"Uploaded {len(uploaded_regions)} regions: {uploaded_regions}")
    else:
        logger.info("No new regions detected")


if __name__ == "__main__":
    main()
