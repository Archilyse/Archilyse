import uuid
from typing import Any, Optional, Type

import ifcopenshell

from handlers.ifc.types import IfcOwnerHistory, IfcRoot


class IfcRootGenerator:
    @classmethod
    def _generate_ifc_entity(
        cls,
        ifc_file,
        ifc_entity_type: Type[IfcRoot],
        GlobalId: Optional[Any] = None,
        OwnerHistory: Optional[IfcOwnerHistory] = None,
        Name: Optional[str] = None,
        Description: Optional[str] = None,
        *args,
        **kwargs,
    ) -> IfcRoot:
        if not GlobalId:
            GlobalId = ifcopenshell.guid.compress(uuid.uuid1().hex)

        if not OwnerHistory:
            OwnerHistory = ifc_file.by_type(IfcOwnerHistory.__name__)[0]

        return ifc_file.create_entity(
            ifc_entity_type.__name__,
            GlobalId=GlobalId,
            OwnerHistory=OwnerHistory,
            Name=Name,
            Description=Description,
            *args,
            **{k: v for k, v in kwargs.items() if v is not None},
        )
