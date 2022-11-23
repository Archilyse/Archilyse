import { FloorplanEditorComponent } from '../../_shared-components/floorplan/floorplan-editor.component';
import { EditorAnalysis } from '../../_shared-libraries/EditorAnalysis';
import { EditorConstants } from '../../_shared-libraries/EditorConstants';
import { FloorplanUnitsLib } from '../../_shared-components/floorplan/floorplan-units-lib';
import { FloorplanIdManager } from './floorplanIdManager';
import { errorHighlightMaterial, errorMaterial } from '../../_shared-libraries/EditorMaterials';

/**
 * This class implements methods that are common to all the Floorplan Services
 */
export class FloorplanCommonLib {
  /**
   * Standar behaviour when we mouse over an element (gets a little darker)
   * @param floorplan
   * @param mesh
   * @param newOpacity
   */
  public static highlightMaterialOverStandar(floorplan: FloorplanEditorComponent, mesh, newOpacity: number) {
    const newColor = mesh.material.color.clone();
    newColor.r -= 0.3;
    newColor.g -= 0.3;
    newColor.b -= 0.3;

    return {
      newColor,
      newOpacity,
    };
  }

  /**
   * The service responds to areas that were removed
   * @param floorplan - The component
   */
  public static subscribeToRemoveAreas(floorplan: FloorplanEditorComponent) {
    if (!floorplan.removeAreasSubscription) {
      floorplan.removeAreasSubscription = floorplan.editorService.removedApartmentAreas.subscribe(removedAreas => {
        if (removedAreas) {
          removedAreas.forEach(removedAreaId => {
            const areaBrooks = floorplan.areaService.getAreaByAreaId(removedAreaId);
            const areaMesh = FloorplanIdManager.getMeshById(floorplan.logic, areaBrooks.id);
            const areaMeshData = FloorplanIdManager.getMeshObjectData(floorplan.logic, areaMesh);
            const newApartment = null;
            const floorNr = EditorConstants.DEFAULT_FLOOR;

            FloorplanUnitsLib.changeApartmentNr(
              floorplan,
              newApartment,
              floorNr,
              areaMesh,
              areaMeshData,
              true,
              null,
              removedAreaId
            );
          });
        }
      });
    }
  }

  /**
   * Subscribe to apartmentChange to react highlighting the selected Unit
   * @param floorplan - The component
   */
  public static subscribeToApartmentChange(floorplan: FloorplanEditorComponent) {
    if (!floorplan.nextSelectedApartmentSubscription) {
      floorplan.nextSelectedApartmentSubscription = floorplan.editorService.nextSelectedApartment.subscribe(
        unitData => {
          if (unitData) {
            const floorNr = unitData.floorNr;
            const apartment = unitData.apartment;

            if (floorplan.logic.renderUnits) {
              const mesh = floorplan.logic.idToUnit[apartment];
              FloorplanUnitsLib.highlightUnit(floorplan, mesh);
            } else {
              FloorplanUnitsLib.restoreUnitMaterialOver(floorplan.selectedMeshes, floorplan.previousMaterials);
              FloorplanUnitsLib.highlightUnitAsAreas(floorplan, apartment, floorNr);
              FloorplanUnitsLib.drawClientIdText(floorplan, apartment);
            }
          }
        }
      );
    }
  }

  /**
   * When the areas of an unit/apartment change we take action.
   * @param floorplan
   * @param reactionToArea -function to execute
   */
  public static subscribeToApartmentAreas(floorplan: FloorplanEditorComponent, reactionToArea) {
    if (!floorplan.getAreasSubscription) {
      floorplan.getAreasSubscription = floorplan.editorService.getApartmentAreas.subscribe(newAreas => {
        if (newAreas) {
          newAreas.forEach(newArea => {
            if (newArea?.area_ids) {
              reactionToArea(newArea);
            }
          });
        }
      });
    }
  }

  /**
   * IF the user wants to highlight an error we react to the event finding the error and
   * giving it other color and size for a short time
   * @param floorplan
   */
  public static subscribeToError(floorplan: FloorplanEditorComponent) {
    if (!floorplan.errorSubscription) {
      floorplan.errorSubscription = floorplan.editorService.highlightError.subscribe(brooksError => {
        if (brooksError) {
          const mesh = FloorplanIdManager.getErrorByIndex(floorplan.logic, brooksError.index);
          if (mesh) {
            const scaleIncrease = 3; // x3

            mesh.scale.x = scaleIncrease;
            mesh.scale.y = scaleIncrease;

            mesh.material = errorHighlightMaterial;

            floorplan.forceRender();

            // Back to normal after 1.5 seconds
            setTimeout(() => {
              mesh.scale.x = 1;
              mesh.scale.y = 1;

              // Restore color
              mesh.material = errorMaterial;

              floorplan.forceRender();
            }, 1500);
          }
        }
      });
    }
  }

  /**
   * Changes the aspect of the floorplan to be highlighted
   * @param element
   * @param objData
   */
  public static highlightElement(element, objData = null) {
    let highlightZoom = 1.4;

    // We make very small objects much bigger so they are easier to spot
    const minPixelsToZoom = 25000;

    if (objData) {
      const elementArea = EditorAnalysis.calculateAreaElement(objData);
      if (elementArea < minPixelsToZoom) {
        highlightZoom = Math.sqrt(minPixelsToZoom / elementArea);
      }
    }

    element.scale.set(highlightZoom, highlightZoom, 1);
    element.material.transparent = false;

    // We change the emissives to have a bright color
    // We'll restore the emissives with the material.color, that has the same original values
    element.material.emissive.r = 0.3;
    element.material.emissive.g = 0.3;
    element.material.emissive.b = 0.8;
  }
}
