import { FloorplanInterfaceService } from './floorplan.interface.service';
import { FloorplanEditorComponent } from '../../_shared-components/floorplan/floorplan-editor.component';
import { EditorConstants, isAnArea } from '../../_shared-libraries/EditorConstants';

import { Mesh, TextGeometry } from 'three-full/builds/Three.es.js';
import { FloorplanCommonLib } from './floorplan.common.lib';
import { FloorplanUnitsLib } from '../../_shared-components/floorplan/floorplan-units-lib';
import { FloorplanIdManager } from './floorplanIdManager';
import { AreaService } from '../area.service';
import { hasOwnNestedProperty } from '../../_shared-libraries/Validations';
import { textErrorMaterial, textMaterial } from '../../_shared-libraries/EditorMaterials';

export class FloorplanSplittingService implements FloorplanInterfaceService {
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
    const textName = areaService.getAreaTypeByElement(originalObject);
    const text = new TextGeometry(textName, {
      size: textSize * 0.25,
      height: 1,
      curveSegments: 1,
      font: fontThree,
      bevelEnabled: false,
    });

    text.center();
    const textMesh = new Mesh(
      text,
      originalObject.type === EditorConstants.AREA_NOT_DEFINED ? textErrorMaterial : textMaterial
    );
    textMesh.position.set(0, 0, zIndex + 4);
    container.add(textMesh);
  }

  clickMaterialArea(floorplan: FloorplanEditorComponent, event, material, color, objectData) {
    const newApartment = floorplan.editorService.nextSelectedApartmentSource.getValue();
    if (newApartment) {
      const floorNr = newApartment.floorNr;
      const apartment = newApartment.apartment;

      let areaId = null;
      if (floorplan.areaService && hasOwnNestedProperty(objectData, 'data.object.id')) {
        const areaInfo = floorplan.areaService.getAreaInfo(null, objectData.data.object.id);
        areaId = areaInfo.id;
      }
      FloorplanUnitsLib.changeApartmentNr(floorplan, apartment, floorNr, material, objectData, true, null, areaId);
    }
  }

  /**
   * Key 'm' highlight the undefined areas
   * @param floorplan
   * @param event
   * @param keyCode
   */
  handleKeyDown(floorplan: FloorplanEditorComponent, event, keyCode: string) {
    if (keyCode === 'm') {
      floorplan.objectsToIntersect.forEach(oTI => {
        if (oTI && oTI.parent && oTI.parent.userData) {
          // In splitting, we hide the already splitted
          if (
            isAnArea(oTI.parent.userData.type) &&
            !(oTI.parent.userData.sel_apartment >= 0 && oTI.parent.userData.sel_apartment !== null)
          ) {
            FloorplanCommonLib.highlightElement(oTI, oTI.parent.userData);
          } else {
            oTI.visible = false;
          }
        }
      });
    }
  }

  handleKeyUp(floorplan: FloorplanEditorComponent, e) {
    // We do nothing
  }

  highlightMaterial(floorplan: FloorplanEditorComponent, mesh) {
    // We do nothing
  }

  highlightMaterialOver(floorplan: FloorplanEditorComponent, mesh) {
    const newOpacity = 0.6;

    floorplan.previousMeshOverMaterial = mesh.material;
    floorplan.previousMeshOver = mesh;

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
        const areaMeshData = FloorplanIdManager.getMeshObjectData(this, areaMesh);

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
      });
    });
  }
}
