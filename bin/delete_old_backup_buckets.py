from tqdm import tqdm

from common_utils.logger import logger
from handlers import GCloudStorageHandler
from handlers.db import ClientDBHandler
from handlers.utils import get_client_bucket_name

if __name__ == "__main__":
    gcloud_handler = GCloudStorageHandler()
    to_manual_delete = []
    for client in tqdm(ClientDBHandler.find(output_columns=["id"])):
        client_bucket_name = get_client_bucket_name(client_id=client["id"])
        try:
            gcloud_handler.delete_bucket_if_exists(f"backup_{client_bucket_name}")
        except ValueError:
            to_manual_delete.append(client["id"])
    logger.info(to_manual_delete)
