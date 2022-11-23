import { FloorplanEditorDraw } from './floorplan-editor-draw';
import { EditorService } from '../../_services/editor.service';
import { FloorplanEditorComponent } from './floorplan-editor.component';
import { FloorplanAreasLib } from './floorplan-areas-lib';
import { EditorMath } from '../../_shared-libraries/EditorMath';
import { MeshPhongMaterial, Group } from 'three-full/builds/Three.es.js';
import { FloorplanIdManager } from '../../_services/floorplan/floorplanIdManager';

export class FloorplanUnitsLib {
  /**
   * Reaction to the user clicking in a unit.
   * The unit get highlighted
   * @param component
   * @param objectData
   */
  public static clickUnit(component: FloorplanEditorComponent, objectData) {
    const editorService: EditorService = component.editorService;

    const { sel_apartment: unitNumber, floorNr: floorNr } = objectData.data.object;
    editorService.setSelectedApartment(unitNumber, floorNr);
    FloorplanUnitsLib.restoreUnitMaterialOver(component.selectedMeshes, component.previousMaterials);
    FloorplanUnitsLib.highlightUnitAsAreas(component, unitNumber, floorNr);
  }

  /**
   * Finds the unit with apartment_no equals to the provided unitNumber
   * @param editorService
   * @param unitNumber
   */
  public static findUnit(editorService: EditorService, unitNumber) {
    const units = editorService.getApartmentAreasSource.getValue();
    return (units || []).find(unit => unit.apartment_no === unitNumber);
  }

  static highlightUnit(floorplan: FloorplanEditorComponent, mesh) {
    if (mesh && mesh.material) {
      FloorplanUnitsLib.restoreUnitMaterialOver(floorplan.selectedMeshes, floorplan.previousMaterials);
      floorplan.previousMaterials = [mesh.material];
      const result = floorplan.logic.highlightMaterialOver(floorplan, mesh);
      mesh.material = new MeshPhongMaterial({
        color: result.newColor,
        emissive: result.newColor,
        transparent: true,
        opacity: result.newOpacity,
      });
      floorplan.selectedMeshes = [mesh];
      floorplan.forceRender();
    }
  }

  /**
   * Given the unit and the floor highlights the corresponding Unit
   * @param component
   * @param unitNumber
   * @param floorNr
   */
  public static highlightUnitAsAreas(component: FloorplanEditorComponent, unitNumber, floorNr) {
    const selectedUnit = FloorplanUnitsLib.findUnit(component.editorService, unitNumber);
    if (!selectedUnit) {
      return;
    }
    selectedUnit.area_ids.forEach(areaId => {
      const areaBrooks = component.areaService.getAreaByAreaId(areaId);
      const mesh = FloorplanIdManager.getMeshById(component.logic, areaBrooks.id);

      if (mesh) {
        if (component.selectedMeshes) {
          if (component.selectedMeshes.includes(mesh)) {
            // We have already highlighted it
            return;
          }
          component.selectedMeshes.push(mesh);
        }
        component.previousMaterials.push(mesh.material);
        FloorplanAreasLib.highlightMaterialOver(component, mesh);
      } else {
        console.error('mesh', mesh, areaId, floorNr);
      }
    });
  }

  /**
   * For all the selectedMeshes recovers the original material (color) they have originally.
   * @param selectedMeshes
   * @param previousMaterials
   */
  public static restoreUnitMaterialOver(selectedMeshes, previousMaterials) {
    if (selectedMeshes.length) {
      selectedMeshes.forEach((mesh, i) => {
        mesh.material = previousMaterials[i];
      });

      // We empty the arrays
      selectedMeshes.length = 0;
      previousMaterials.length = 0;
    }
  }

  /**
   *
   * @param component
   * @param newApartment
   * @param floorNr
   * @param areaMesh
   * @param areaMeshData
   * @param manualChanged
   * @param floorId
   * @param areaId
   */
  public static changeApartmentNr(
    component: FloorplanEditorComponent,
    newApartment,
    floorNr,
    areaMesh,
    areaMeshData,
    manualChanged: boolean,
    floorId,
    areaId
  ) {
    const element = areaMeshData.data.object;
    const oldApartment = element.sel_apartment;

    // Change apartment
    element.floorNr = floorNr;
    element.sel_apartment = newApartment;

    component.editorService.changedApartmentNr(element, oldApartment, newApartment, manualChanged, floorId, areaId);

    FloorplanAreasLib.redrawArea(component, areaMesh, element, floorNr);
  }

  /**
   * Draws the client Id text in the center of the unit.
   * @param component
   * @param unitNumber
   */
  public static drawClientIdText(component: FloorplanEditorComponent, unitNumber) {
    if (!unitNumber) {
      return;
    }
    component.scene.remove(component.textGroups[unitNumber]);

    const unit = FloorplanUnitsLib.findUnit(component.editorService, unitNumber);
    if (!unit) {
      return;
    }

    try {
      let areaMesh = null;
      let biggerAreaSize = 0.0;
      for (let i = 0; i < unit.area_ids.length; i += 1) {
        const areaBrooks = component.areaService.getAreaByAreaId(unit.area_ids[i]);
        const area_size = EditorMath.calculateAreaFromPolygon(areaBrooks.footprint);
        if (area_size > biggerAreaSize) {
          biggerAreaSize = area_size;
          areaMesh = FloorplanIdManager.getMeshById(component.logic, areaBrooks.id);
        }
      }

      if (areaMesh) {
        const meshData = FloorplanIdManager.getMeshObjectData(component.logic, areaMesh);
        if (meshData) {
          const areaPolygons = areaMesh.parent.parent;
          const { x, y, z } = areaPolygons.position;
          const textGroup = new Group();
          textGroup.position.set(x, y, z);
          component.scene.add(textGroup);
          component.textGroups[unitNumber] = textGroup;

          const areaSurface = EditorMath.calculateAreaFromPolygon(meshData.data.areaData);
          const DEFAULT_CLIENT_ID_TEXT = 'client id';
          FloorplanEditorDraw.drawText(
            unit.client_id || DEFAULT_CLIENT_ID_TEXT,
            textGroup,
            component._font3d,
            areaSurface
          );
          component.render();
        } else {
          console.error('meshData not found ', areaMesh);
        }
      } else {
        console.error('firstAreaMesh not found ', unit.area_ids);
      }
    } catch (e) {
      console.error(e);
    }
  }

  /**
   *
   * @param logic
   * @param newArea
   * @param floorplan
   */
  static assignAreasToUnit(logic, newArea, floorplan) {
    newArea.area_ids.forEach(areaIds => {
      const floorNr = newArea.floor_id;
      const areaMesh = FloorplanIdManager.getAreaByIdAndFloorNr(logic, areaIds, floorNr);
      const areaMeshData = FloorplanIdManager.getMeshObjectData(logic, areaMesh);

      const newApartment = newArea.apartment_no;
      FloorplanUnitsLib.changeApartmentNr(
        floorplan,
        newApartment,
        floorNr,
        areaMesh,
        areaMeshData,
        false,
        newArea.floor_id,
        areaIds
      );
    });
  }
}
