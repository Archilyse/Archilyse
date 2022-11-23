from pathlib import Path

from handlers import DMSVectorFilesHandler
from handlers.db import SiteDBHandler

outputfolder = (
    Path().home().joinpath("Downloads/PH_DELIVERY")
)  # Outputfolder needs to exist
site_id = 4265

subgroups = {
    "0": {"60330"},
    "1": {"60331", "60328", "60334"},
    "2": {"60332", "60336", "60338", "60339"},
}  # keys are the prefixes added additionally to the outputfiles to discriminate between the subgroups. The values containing a set of strings. If a unit client
# id contains that string the unit is added to this subgroup


DMSVectorFilesHandler._generate_vector_files(
    site=SiteDBHandler.get_by(id=site_id),
    folderpath=outputfolder,
    representative_units_only=False,
    subgroups=subgroups,
)
