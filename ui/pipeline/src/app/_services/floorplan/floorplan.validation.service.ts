import { FloorplanInterfaceService } from './floorplan.interface.service';
import { FloorplanEditorComponent } from '../../_shared-components/floorplan/floorplan-editor.component';
import { EditorConstants, isAnArea } from '../../_shared-libraries/EditorConstants';

import { FloorplanCommonLib } from './floorplan.common.lib';
import { AreaService } from '../area.service';

export class FloorplanValidationService implements FloorplanInterfaceService {
  uuidToObject = {};
  idToObject = {};
  idAndFloorToArea = {};
  idToUnit = {};
  indexToError = {};

  analyzeStructureColorAreas(floorplan: FloorplanEditorComponent, structure) {
    if (isAnArea(structure.type)) {
      return [EditorConstants.COLORS_HEX[Math.floor(Math.random() * EditorConstants.COLORS_HEX.length)]];
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
  ) {}

  clickMaterialArea(floorplan: FloorplanEditorComponent, event, material, color, objectData) {
    // We do nothing
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
    // Nothing has to be done
  }
}
