import time
import uuid
from pathlib import Path

import ifcopenshell
from jinja2 import Template


def create_ifc_guid() -> str:
    return ifcopenshell.guid.compress(uuid.uuid1().hex)


def default_ifc_template(project_name: str) -> str:
    # IFC template creation
    timestamp = time.time()
    # A template IFC file to quickly populate entity instances for an IfcProject with its dependencies
    with Path(__file__).parent.absolute().joinpath(
        "templates/ifc_base_template.j2"
    ).open("r") as f:
        time_formatted = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(timestamp))
        return Template(f.read()).render(
            site_name=project_name,
            timestring=time_formatted,
            organization="Archilyse",
            project_globalid=create_ifc_guid(),
            timestamp=int(timestamp),
            application="Archilyse Digitize",
            application_version="1.0",
        )
