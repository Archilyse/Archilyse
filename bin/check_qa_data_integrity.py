from collections import defaultdict

from tqdm import tqdm

from common_utils.logger import logger
from handlers.db import QADBHandler, SiteDBHandler


def fix_qa_integrity_issues(client_id=1):
    stats = check_qa_integrity(client_id=client_id)

    # First we remove the entries that are linked to sites not existing anymore (site_linked_not_found)
    for _, qa_id in stats["site_linked_not_found"]:
        QADBHandler.delete(item_pk={"id": qa_id})

    # DEDUPLICATION
    for site_id, _ in stats["site_id_repeated"]:
        site_info = SiteDBHandler.get_by(
            id=site_id, output_columns=["client_site_id", "id"]
        )
        qa_entries_to_delete = [
            x
            for x in QADBHandler.find(
                site_id=site_id, output_columns=["id", "client_site_id", "created"]
            )
            if x["client_site_id"] != site_info["client_site_id"]
        ]
        for qa_entry in qa_entries_to_delete:
            QADBHandler.delete(item_pk={"id": qa_entry["id"]})

    # remove orphan qa entries if no sites pending
    if len(stats["site_id_not_linked"]) == 0 and len(stats["qa_no_site"]) > 0:
        for _, qa_id in stats["qa_no_site"]:
            QADBHandler.delete(item_pk={"id": qa_id})

    # Update qa entries to the correct client_site_id
    for qa_id, _, correct_client_site_id in stats[
        "unique_site_linked_found_but_different_client_site_id_on_qa"
    ]:
        QADBHandler.update(
            item_pks=dict(id=qa_id),
            new_values=dict(client_site_id=correct_client_site_id),
        )


def check_qa_integrity(client_id=1):
    stats = defaultdict(set)
    site_ids_linked = defaultdict(set)
    sites_info = {
        site["id"]: site
        for site in SiteDBHandler.find(
            client_id=client_id, output_columns=["client_site_id", "id"]
        )
    }
    for qa_entry in tqdm(
        QADBHandler.find(
            client_id=client_id, output_columns=["id", "site_id", "client_site_id"]
        )
    ):
        #         1 if qa entry have no site_id linked
        if not qa_entry["site_id"]:
            stats["qa_no_site"].add((qa_entry["client_site_id"], qa_entry["id"]))
        #         2 if site_id is linked but not found in sites_info
        elif qa_entry["site_id"] not in sites_info:
            stats["site_linked_not_found"].add(
                (qa_entry["client_site_id"], qa_entry["id"])
            )
        #         3 if site_id is linked and found in sites_info but client_site_id is different
        elif (
            qa_entry["client_site_id"]
            != sites_info[qa_entry["site_id"]]["client_site_id"]
        ):
            stats["unique_site_linked_found_but_different_client_site_id_on_qa"].add(
                (
                    qa_entry["id"],
                    qa_entry["site_id"],
                    sites_info[qa_entry["site_id"]]["client_site_id"],
                )
            )
        #       4 if site_id is repeated more than once
        if qa_entry["site_id"]:
            site_ids_linked[qa_entry["site_id"]].add(qa_entry["client_site_id"])

    # Check for repeated site_ids
    for site_id, client_site_ids in site_ids_linked.items():
        if len(client_site_ids) > 1:
            stats["site_id_repeated"].add((site_id, ",".join(client_site_ids)))

    # clean from unique_site_linked_found_but_different_client_site_id_on_qa the duplicated ones
    # (they are already in site_id_repeated)
    for site_id, _ in stats["site_id_repeated"]:
        stats["unique_site_linked_found_but_different_client_site_id_on_qa"] = {
            x
            for x in stats[
                "unique_site_linked_found_but_different_client_site_id_on_qa"
            ]
            if x[1] != site_id
        }

    #      we check if some site id does not have any qa entry linked
    stats["site_id_not_linked"] = set(sites_info.keys()) - set(site_ids_linked.keys())

    logger.info(stats)
    return stats
