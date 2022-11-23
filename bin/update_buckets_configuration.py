from google.cloud.exceptions import NotFound
from tqdm import tqdm

from handlers import GCloudStorageHandler
from handlers.db import ClientDBHandler
from handlers.utils import get_client_bucket_name

if __name__ == "__main__":
    gcloud_handler = GCloudStorageHandler()
    for client in tqdm(ClientDBHandler.find(output_columns=["id"])):
        client_bucket_name = get_client_bucket_name(client_id=client["id"])
        try:
            bucket = gcloud_handler.client.get_bucket(client_bucket_name)
        except NotFound:
            continue
        bucket.versioning_enabled = True
        bucket.add_lifecycle_delete_rule(number_of_newer_versions=2, is_live=False)
        bucket.add_lifecycle_delete_rule(days_since_noncurrent_time=14)
        bucket.patch()
