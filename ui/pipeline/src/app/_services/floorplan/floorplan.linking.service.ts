import { FloorplanInterfaceService } from './floorplan.interface.service';
import { FloorplanEditorComponent } from '../../_shared-components/floorplan/floorplan-editor.component';
import { EditorConstants, isAnArea } from '../../_shared-libraries/EditorConstants';
import { FloorplanCommonLib } from './floorplan.common.lib';
import { FloorplanUnitsLib } from '../../_shared-components/floorplan/floorplan-units-lib';
import { FloorplanIdManager } from './floorplanIdManager';
import { AreaService } from '../area.service';

export class FloorplanLinkingService implements FloorplanInterfaceService {
  highlightUnits = true;

  uuidToObject = {};
  idToObject = {};
  idAndFloorToArea = {};
  idToUnit = {};
  indexToError = {};

  analyzeStructureColorAreas(floorplan: FloorplanEditorComponent, structure) {
    if (isAnArea(structure.type)) {
      if (structure.sel_apartment >= 0 && structure.sel_apartment !== null) {
        return [EditorConstants.COLORS_HEX[structure.sel_apartment % EditorConstants.COLORS_HEX.length]];
      }
    }

    // Default color
    return null;
  }

  drawPolygonsAreas(
    areaService: AreaService,
    container,
    areaSurface: number,
    textSize: number,
    editorScale: number,
    originalObject,
    fontThree,
    segmentMesh,
    zIndex
  ) {
    // We don't do nothing extra
  }

  clickMaterialArea(floorplan: FloorplanEditorComponent, event, material, color, objectData) {
    floorplan.clickUnit(objectData);
  }

  handleKeyDown(floorplan: FloorplanEditorComponent, event, keyCode: string) {
    // We do nothing
  }

  handleKeyUp(floorplan: FloorplanEditorComponent, e) {
    // We do nothing
  }

  highlightMaterial(floorplan: FloorplanEditorComponent, mesh) {
    // We do nothing
  }

  highlightMaterialOver(floorplan: FloorplanEditorComponent, mesh) {
    const newOpacity = 0.7;
    return FloorplanCommonLib.highlightMaterialOverStandar(floorplan, mesh, newOpacity);
  }

  restoreMaterial(floorplan: FloorplanEditorComponent) {
    // We do nothing
  }

  restoreMaterialOver(floorplan: FloorplanEditorComponent, newMesh) {
    // Nothing has to be done
  }

  subscribeToServices(floorplan: FloorplanEditorComponent) {
    FloorplanCommonLib.subscribeToRemoveAreas(floorplan);
    FloorplanCommonLib.subscribeToApartmentAreas(floorplan, newArea => {
      newArea.area_ids.forEach(areaId => {
        const areaBrooks = floorplan.areaService.getAreaByAreaId(areaId);
        const areaMesh = FloorplanIdManager.getMeshById(this, areaBrooks.id);
        if (areaMesh) {
          const areaMeshData = FloorplanIdManager.getMeshObjectData(this, areaMesh);
          if (areaMeshData) {
            const newApartment = newArea.apartment_no;
            const floorNr = EditorConstants.DEFAULT_FLOOR;
            FloorplanUnitsLib.changeApartmentNr(
              floorplan,
              newApartment,
              floorNr,
              areaMesh,
              areaMeshData,
              false,
              newArea.floor_id,
              areaId
            );
          } else {
            console.error('areaMeshData not found', areaMeshData);
          }
        } else {
          console.error('areaMesh not found', areaMesh, areaId);
        }
      });
      FloorplanUnitsLib.drawClientIdText(floorplan, newArea.apartment_no);
    });
    FloorplanCommonLib.subscribeToApartmentChange(floorplan);
  }
}
