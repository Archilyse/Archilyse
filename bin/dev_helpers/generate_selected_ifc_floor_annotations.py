from dataclasses import asdict
from pathlib import Path

from handlers import PlanHandler
from handlers.db import PlanDBHandler, ReactPlannerProjectsDBHandler, SiteDBHandler
from handlers.editor_v2 import ReactPlannerHandler
from handlers.ifc import IfcToSiteHandler
from handlers.ifc.importer.ifc_storey_handler import IfcStoreyHandler
from handlers.ifc.importer.ifc_to_react_planner_mapper import IfcToReactPlannerMapper
from handlers.utils import get_client_bucket_name
from ifc_reader.constants import IFC_BUILDING, IFC_STOREY
from ifc_reader.reader import IfcReader

ifc_reader = IfcReader(filepath=Path().home().joinpath("Downloads/UFBA_TN01_BEM.ifc"))
update_background_image = True
plan_id = 58

ifc_handler = IfcToSiteHandler(ifc_reader=ifc_reader)
building = ifc_handler.ifc_reader.wrapper.by_type(IFC_BUILDING)[0]
storey_id = ifc_reader.wrapper.by_type(IFC_STOREY)[16].id()


storey_handler = IfcStoreyHandler(ifc_reader=ifc_reader)
data = IfcToReactPlannerMapper(
    ifc_storey_handler=storey_handler
).get_react_planner_data_from_ifc_storey(
    storey_id=storey_id,
)

planner_db_data = ReactPlannerHandler().get_by_migrated(plan_id=plan_id)
ReactPlannerProjectsDBHandler.update(
    item_pks={"id": planner_db_data["id"]},
    new_values={"data": asdict(data)},
)

if update_background_image:
    plan_handler = PlanHandler(plan_id=plan_id)
    output_stream = storey_handler.storey_figure(
        building_id=building.GlobalId, storey_id=storey_id
    )
    image_gc_link = plan_handler.upload_plan_image_to_google_cloud(
        image_data=output_stream.read(),
        destination_bucket=get_client_bucket_name(
            client_id=SiteDBHandler.get_by(id=plan_handler.site_info["id"])["client_id"]
        ),
    )
    PlanDBHandler.update(
        item_pks={"id": plan_id}, new_values={"image_gcs_link": image_gc_link}
    )
