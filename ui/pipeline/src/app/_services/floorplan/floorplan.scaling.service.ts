import { FloorplanInterfaceService } from './floorplan.interface.service';
import { FloorplanEditorComponent } from '../../_shared-components/floorplan/floorplan-editor.component';
import { EditorMath } from '../../_shared-libraries/EditorMath';
import { isAnArea } from '../../_shared-libraries/EditorConstants';

import { Mesh, TextGeometry } from 'three-full/builds/Three.es.js';
import { FloorplanAreasLib } from '../../_shared-components/floorplan/floorplan-areas-lib';
import { AreaService } from '../area.service';
import { textMaterial } from '../../_shared-libraries/EditorMaterials';

export class FloorplanScalingService implements FloorplanInterfaceService {
  uuidToObject = {};
  idToObject = {};
  idAndFloorToArea = {};
  idToUnit = {};
  indexToError = {};

  analyzeStructureColorAreas(floorplan: FloorplanEditorComponent, structure) {
    if (isAnArea(structure.type)) {
      return [0xddcccc];
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
    if (areaSurface > 1) {
      const text = new TextGeometry(`${Math.round(areaSurface * editorScale * 10) / 10} m2`, {
        size: textSize * 0.4,
        height: 1,
        curveSegments: 1,
        font: fontThree,
        bevelEnabled: false,
      });
      text.center();
      const textMesh = new Mesh(text, textMaterial);
      textMesh.position.set(0, 0, zIndex + 4);
      container.add(textMesh);
    }
  }

  clickMaterialArea(floorplan: FloorplanEditorComponent, event, material, color, objectData) {
    const areaSurface = EditorMath.calculateAreaFromPolygon(objectData.data.areaData);

    floorplan.editorService.setScale(areaSurface);
  }

  handleKeyDown(floorplan: FloorplanEditorComponent, event, keyCode: string) {
    // We do nothing
  }

  handleKeyUp(floorplan: FloorplanEditorComponent, e) {
    // We do nothing
  }

  highlightMaterial(floorplan: FloorplanEditorComponent, mesh) {
    FloorplanAreasLib.highlightMaterialLogic(floorplan, mesh);
  }

  highlightMaterialOver(floorplan: FloorplanEditorComponent, mesh) {
    /** Color when mouse over */
    const newColor = 0xff99;
    const newOpacity = 0.5;

    floorplan.previousMeshOverMaterial = mesh.material;
    floorplan.previousMeshOver = mesh;

    return {
      newColor,
      newOpacity,
    };
  }

  restoreMaterial(floorplan: FloorplanEditorComponent) {
    if (floorplan.previousMesh !== null) {
      floorplan.previousMesh.material = floorplan.previousMeshMaterial;
      floorplan.previousMesh = null;
    }
    floorplan.forceRender();
  }

  restoreMaterialOver(floorplan: FloorplanEditorComponent, newMesh) {
    // Nothing has to be done
  }

  subscribeToServices(floorplan: FloorplanEditorComponent) {
    // Default behaviour
  }
}
