import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZipFile

from handlers.editor_v2 import ReactPlannerHandler
from handlers.editor_v2.schema import ReactPlannerSchema


def remove_from_zip(zipfname, *filenames):
    tempdir = tempfile.mkdtemp()
    try:
        tempname = os.path.join(tempdir, "new.zip")
        with zipfile.ZipFile(zipfname, "r") as zipread:
            with zipfile.ZipFile(tempname, "w") as zipwrite:
                for item in zipread.infolist():
                    if item.filename not in filenames:
                        data = zipread.read(item.filename)
                        zipwrite.writestr(item, data)
        shutil.move(tempname, zipfname)
    finally:
        shutil.rmtree(tempdir)


if __name__ == "__main__":
    for file in Path("tests/fixtures/annotations/").rglob("*.json"):
        overwrite = False
        with file.open() as f:
            plan_data = json.load(f)
            initial_version = plan_data["version"]
            migrated_plan = ReactPlannerHandler.migrate_data_if_old_version(
                plan_data=plan_data
            )
            ReactPlannerSchema().load(migrated_plan).validate()
            if initial_version != migrated_plan["version"]:
                overwrite = True
        if overwrite:
            with file.open("wt") as f:
                json.dump(migrated_plan, f)

    zip_file_and_file_content = {
        "tests/fixtures/dashboard/implenia_fixture/annotations.zip": "annotations.json",
        "tests/fixtures/site_1440.zip": "react_planner_projects.json",
    }
    for zip_folder_name, annotations_file in zip_file_and_file_content.items():
        overwrite = False
        with ZipFile(zip_folder_name) as fixture_zip:
            with fixture_zip.open(annotations_file) as myfile:
                content = json.load(myfile)
                migrated_plans = []
                for plan in content:
                    initial_version = plan["data"]["version"]
                    migrated_plan = ReactPlannerHandler.migrate_data_if_old_version(
                        plan_data=plan["data"]
                    )
                    ReactPlannerSchema().load(migrated_plan).validate()
                    if initial_version != migrated_plan["version"]:
                        overwrite = True
                        plan["data"] = migrated_plan
                        migrated_plans.append(plan)

        if overwrite:
            remove_from_zip(zip_folder_name, annotations_file)
            with zipfile.ZipFile(
                zip_folder_name, "a", zipfile.ZIP_DEFLATED
            ) as zip_folder_file:
                with NamedTemporaryFile() as temp_file:
                    temp_file.write(json.dumps(migrated_plans).encode())
                    zip_folder_file.write(
                        filename=temp_file.name, arcname=annotations_file
                    )
