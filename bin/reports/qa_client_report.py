import click
from pandas import DataFrame, concat
from tqdm import tqdm

from common_utils.constants import ADMIN_SIM_STATUS
from common_utils.logger import logger
from handlers import QAHandler
from handlers.db import SiteDBHandler


@click.command()
@click.option("--client_id", "-s", prompt=True, type=click.INT)
def qa_report(client_id: int):
    report_path = f"qa_{client_id}_report.csv"
    report = DataFrame()

    for site in tqdm(
        SiteDBHandler.find(
            client_id=client_id,
            full_slam_results=ADMIN_SIM_STATUS.SUCCESS,
            output_columns=["id"],
        )
    ):
        report = concat([report, QAHandler(site_id=site["id"]).generate_qa_report()])

    report.to_csv(report_path, mode="w")
    logger.info(f"Saved at {report_path}")


if __name__ == "__main__":
    qa_report()
