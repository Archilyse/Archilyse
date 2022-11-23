import click
from pandas import concat
from tqdm import tqdm

from common_utils.constants import ADMIN_SIM_STATUS
from common_utils.exceptions import SimulationNotSuccessException
from common_utils.logger import logger
from handlers import QAHandler
from handlers.db import SiteDBHandler


@click.command()
@click.option("--site_id", "-s", prompt=True, type=click.INT)
def qa_report(site_id: int):
    report_path = f"qa_{site_id}_report.csv"
    QAHandler(site_id=site_id).generate_qa_report().to_csv(report_path)
    logger.info(f"Saved at {report_path}")


def qa_report_client(client_id: int):
    reports_per_sites = []
    for site_id in tqdm(
        list(
            SiteDBHandler.find_ids(
                client_id=client_id, full_slam_results=ADMIN_SIM_STATUS.SUCCESS.name
            )
        )
    ):
        try:
            reports_per_sites.append(QAHandler(site_id=site_id).generate_qa_report())
        except SimulationNotSuccessException as e:
            logger.info(f"Skipping site {site_id} because {e}")

    full_report_client = concat(reports_per_sites)
    report_path = f"qa_full_client_{client_id}_report.csv"
    full_report_client.to_csv(report_path)
    logger.info(f"Saved at {report_path}")


if __name__ == "__main__":
    qa_report()
