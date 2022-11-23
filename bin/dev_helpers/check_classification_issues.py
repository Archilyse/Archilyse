from collections import defaultdict

from tqdm import tqdm

from brooks.types import AreaType
from common_utils.logger import logger
from handlers import AreaHandler
from handlers.db import AreaDBHandler, PlanDBHandler, SiteDBHandler

errors_by_site = defaultdict(list)
for site in tqdm(SiteDBHandler.find(client_id=1, pipeline_and_qa_complete=True)):
    for plan in PlanDBHandler.find(site_id=site["id"]):
        try:
            area_id_to_area_type = {
                area["id"]: AreaType[area["area_type"]]
                for area in AreaDBHandler.find(plan_id=plan["id"])
            }
            violations = AreaHandler.validate_plan_classifications(
                plan_id=plan["id"],
                area_id_to_area_type=area_id_to_area_type,
                only_blocking=True,
            )
            if violations:
                errors_by_site[site["id"]].append(plan["id"])
        except (ValueError, KeyError) as e:
            logger.error(f"WTF: {site['id']}, plan: {plan['id']}. Error: {e}")

logger.info(errors_by_site)
