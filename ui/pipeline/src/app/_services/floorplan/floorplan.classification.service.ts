import { FloorplanInterfaceService } from './floorplan.interface.service';
import { FloorplanEditorComponent } from '../../_shared-components/floorplan/floorplan-editor.component';
import { EditorConstants, isAnArea } from '../../_shared-libraries/EditorConstants';

import { Mesh, TextGeometry } from 'three-full/builds/Three.es.js';
import { EditorControlsVisuals } from '../../_shared-libraries/EditorControlsVisuals';
import { FloorplanCommonLib } from './floorplan.common.lib';
import { FloorplanAreasLib } from '../../_shared-components/floorplan/floorplan-areas-lib';
import { FloorplanIdManager } from './floorplanIdManager';
import { AreaService } from '../area.service';
import { hasOwnNestedProperty } from '../../_shared-libraries/Validations';
import { textErrorMaterial, textMaterial } from '../../_shared-libraries/EditorMaterials';

export class FloorplanClassificationService implements FloorplanInterfaceService {
  uuidToObject = {};
  idToObject = {};
  idAndFloorToArea = {};
  idToUnit = {};
  indexToError = {};

  analyzeStructureColorAreas(floorplan: FloorplanEditorComponent, structure) {
    if (isAnArea(structure.type)) {
      const elType = floorplan.areaService.getAreaTypeByElement(structure);

      for (let i = 0; i < floorplan.areaTypes.length; i += 1) {
        const type = floorplan.areaTypes[i];
        if (elType === type) {
          const areaTypeColors = floorplan.areaService.getColors();
          return [areaTypeColors[i]];
        }
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
    const areaType = areaService.getAreaTypeByElement(originalObject);
    const text = new TextGeometry(areaType, {
      size: textSize * 0.25,
      height: 1,
      curveSegments: 1,
      font: fontThree,
      bevelEnabled: false,
    });

    if (originalObject.type === EditorConstants.AREA_NOT_DEFINED) {
      EditorControlsVisuals.uuidNotDefined[segmentMesh.uuid] = segmentMesh;
    }
    text.center();
    const textMesh = new Mesh(
      text,
      originalObject.type === EditorConstants.AREA_NOT_DEFINED ? textErrorMaterial : textMaterial
    );
    textMesh.position.set(0, 0, zIndex + 4);
    container.add(textMesh);

    // add the m2 hint
    if (areaSurface > 1) {
      const text = new TextGeometry(`${Math.round(areaSurface * editorScale * 10) / 10} m2`, {
        size: textSize * 0.15,
        height: 1,
        curveSegments: 1,
        font: fontThree,
        bevelEnabled: false,
      });
      text.center();
      const textMesh = new Mesh(text, textMaterial);
      textMesh.position.set(0, -0.27 * textSize, zIndex + 4);
      container.add(textMesh);
    }
  }

  clickMaterialArea(floorplan: FloorplanEditorComponent, event, material, color, objectData) {
    const newType = `AreaType.${floorplan.editorService.nextSelectedAreaSource.getValue()}`;

    const element = objectData.data.object;
    const oldType = element.type;

    FloorplanAreasLib.changeApartmentType(floorplan, material, element, oldType, newType);
  }

  handleKeyDown(floorplan: FloorplanEditorComponent, event, keyCode: string) {
    if (keyCode === 'm') {
      floorplan.objectsToIntersect.forEach(oTI => {
        if (hasOwnNestedProperty(oTI, 'parent.userData')) {
          // In classification, we hide the already classified
          if (oTI.parent.userData.type !== EditorConstants.AREA_NOT_DEFINED) {
            oTI.visible = false;
          } else if (isAnArea(oTI.parent.userData.type)) {
            FloorplanCommonLib.highlightElement(oTI, oTI.parent.userData);
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
    if (!floorplan.oldClassSubscription) {
      floorplan.oldClassSubscription = floorplan.editorService.oldClassification.subscribe(oldClass => {
        if (oldClass) {
          // We try to get the threejs mesh by Id
          const areaMesh = FloorplanIdManager.getMeshById(this, oldClass.id);
          let areaMeshData;
          if (areaMesh) {
            // If we have the mesh, we get the data to change
            areaMeshData = FloorplanIdManager.getMeshObjectData(this, areaMesh).data.object;
            FloorplanAreasLib.changeApartmentType(floorplan, areaMesh, areaMeshData, areaMeshData.type, oldClass.type);
          } else {
            console.log('Area not found', oldClass.type, oldClass);
          }
        }
      });
    }
  }
}
