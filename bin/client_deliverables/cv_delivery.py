from pathlib import Path

from common_utils.constants import OUTPUT_DIR
from handlers import DMSVectorFilesHandler
from handlers.db import ClientDBHandler, SiteDBHandler
from tasks.utils.deliverable_utils import _create_path, client_site_id

representative_units_only = True
client_name = "Portfolio Client"
client = ClientDBHandler.get_by(name=client_name)
sites = SiteDBHandler.find(
    client_id=client["id"], full_slam_results="SUCCESS", pipeline_and_qa_complete=True
)

for site in sites:
    client_path = _create_path(base_path=Path(OUTPUT_DIR), postfix=client["name"])
    site_path = _create_path(base_path=client_path, postfix=client_site_id(site))
    DMSVectorFilesHandler._generate_vector_files(
        site=site,
        folderpath=site_path,
        representative_units_only=representative_units_only,
    )
