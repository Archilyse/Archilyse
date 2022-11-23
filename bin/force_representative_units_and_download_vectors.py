from collections import defaultdict
from pathlib import Path

from common_utils.logger import logger
from handlers import DMSVectorFilesHandler, UnitHandler
from handlers.db import ClusteringSubsamplingDBHandler, SiteDBHandler, UnitDBHandler


def update_clustering(force_representative_units):
    for (
        site_id,
        wrongly_clustered_apartments,
    ) in force_representative_units.items():
        logger.info(f"updating clustering for site {site_id}")
        corrected_clustering = defaultdict(list)
        wrong_clustering = defaultdict(list)

        for unit_info in UnitDBHandler.find(
            site_id=site_id,
            output_columns=["client_id", "representative_unit_client_id"],
        ):
            wrong_clustering[unit_info["representative_unit_client_id"]].append(
                unit_info["client_id"]
            )
            if unit_info["client_id"] not in wrongly_clustered_apartments:
                corrected_clustering[unit_info["representative_unit_client_id"]].append(
                    unit_info["client_id"]
                )
            else:
                if unit_info["representative_unit_client_id"] == unit_info["client_id"]:
                    logger.warning(
                        f"unit {unit_info['client_id']} is already representative!"
                    )
                else:
                    logger.info(f"Making unit {unit_info['client_id']} representative.")
                corrected_clustering[unit_info["client_id"]].append(
                    unit_info["client_id"]
                )

        corrected_clustering_db_record = ClusteringSubsamplingDBHandler.add(
            site_id=site_id, results=corrected_clustering
        )
        # we also store the old clustering again just to collect the id to recover the old clusters just in case
        wrong_clustering_db_record = ClusteringSubsamplingDBHandler.add(
            site_id=site_id, results=wrong_clustering
        )

        logger.info("Updating representative units.")
        UnitHandler().update_units_representative(
            site_id=site_id, clustering_id=corrected_clustering_db_record["id"]
        )

        logger.info(f"old clustering: {wrong_clustering_db_record['id']}")
        logger.info(f"new clustering: {corrected_clustering_db_record['id']}")


def download_updated_unit_vectors(subgroups_by_site_id, outputfolder):
    for site_id, subgroups in subgroups_by_site_id.items():
        DMSVectorFilesHandler._generate_vector_files(
            site=SiteDBHandler.get_by(id=site_id),
            folderpath=outputfolder,
            representative_units_only=True,
            subgroups=subgroups,
            subgroups_match_client_ids_exact=True,
            subgroups_allow_subset=True,
        )


wrongly_clustered_apartments_by_site_id = {
    4264: {
        "2006",
        "2004",
        "2005",
        "10.05002",
        "03.05004",
        "03.18001",
        "03.17001",
        "03.22001",
        "03.14005",
        "03.13005",
        "03.18005",
        "03.09005",
        "03.22003",
        "03.16006",
        "03.17006",
        "03.21006",
        "03.22006",
        "03.23006",
        "03.22005",
        "2007",
        "2008",
        "03.14004",
        "03.19004",
        "03.23004",
        "03.09006",
        "03.13006",
        "03.17002",
        "03.21002",
        "03.22002",
        "03.10003",
        "03.14003",
        "03.11007",
        "03.12007",
        "03.16007",
        "03.17007",
        "03.18007",
        "03.22007",
        "03.05005",
        "2001",
        "2002",
    },
    4252: {"02.01.0200", "02.05.0200", "01.09.0500", "01.08.0400"},
}

subgroups_by_site_id = {
    4264: {
        4264: wrongly_clustered_apartments_by_site_id[4264],
    },
    4252: {"N1": {"01.09.0500", "01.08.0400"}, "N2": {"02.01.0200", "02.05.0200"}},
}

if __name__ == "__main__":
    outputfolder = Path().home().joinpath("Downloads/PH_DELIVERY")
    outputfolder.mkdir(exist_ok=True, parents=True)

    update_clustering(
        force_representative_units=wrongly_clustered_apartments_by_site_id
    )
    download_updated_unit_vectors(
        subgroups_by_site_id=subgroups_by_site_id, outputfolder=outputfolder
    )
