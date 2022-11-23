import { MapView } from '@here/harp-mapview';
import C from '../../../constants';
import { COLORED_UNIT_OPACITY, CONTEXT_UNIT_OPACITY, HIGHLIGHTED_UNIT_OPACITY, UNIT_OPACITY } from './SimConstants';
import { calculateDomain } from './SimRenderer';

const getMaxMinPrice = currentUnits =>
  currentUnits.reduce(
    (accum, unit) => {
      const { ph_final_gross_rent_annual_m2: price } = unit;
      if (price > accum.max) accum.max = price;
      if (price < accum.min) accum.min = price;
      return accum;
    },
    { max: -Infinity, min: Infinity }
  );
export class UnitControls {
  unitToMeshes = {};

  map;

  constructor(map: MapView) {
    this.map = map;
  }

  /**
   * The modified unit is displayed as it used to be, restoring color and opacity   *
   */
  restoreInitialUnitsStyle(context3dUnits) {
    Object.keys(this.unitToMeshes).forEach(unitClientId => {
      const meshes = this.unitToMeshes[unitClientId];
      if (!meshes) return;
      const isContextUnit = context3dUnits?.length > 0 ? context3dUnits.includes(unitClientId) : true;
      meshes.forEach(mesh => {
        if (!mesh.children) return;
        const unitMesh = mesh.children[0];
        unitMesh.material.opacity = isContextUnit ? CONTEXT_UNIT_OPACITY : UNIT_OPACITY;
        unitMesh.material.color.set(isContextUnit ? C.DASHBOARD_3D_UNIT_COLOR : C.FADED_UNIT_COLOR);
      });
    });
  }

  areUnitsEqual(unitsA, unitsB) {
    if (!unitsA && !unitsB) {
      return true;
    }
    if (unitsA && unitsB) {
      if (unitsA.length === unitsB.length) {
        unitsA.sort();
        unitsB.sort();
        for (let i = 0; i < unitsA.length; i += 1) {
          if (unitsA[i] !== unitsB[i]) {
            return false;
          }
        }
        return true;
      }
    }
    return false;
  }

  colorizeUnitsByPrice(currentUnits) {
    const { max, min } = getMaxMinPrice(currentUnits);
    const valueToColor = calculateDomain(min, max);

    currentUnits.forEach(unit => {
      const meshes = this.unitToMeshes[unit.client_id];
      if (!meshes) return;

      const rgbColor = valueToColor(unit.ph_final_gross_rent_annual_m2);

      meshes.forEach(mesh => {
        if (!mesh.children) return;
        const unitMesh = mesh.children[0];
        unitMesh.material.opacity = COLORED_UNIT_OPACITY;
        unitMesh.material.color.set(rgbColor);
      });
    });
  }

  /**
   * Finds the unit and changes the color and opacity
   * Stores the modified mesh of the unit to be restored lately
   * @param unitClientIds
   */
  highlightUnits(unitClientIds) {
    if (!unitClientIds) return;
    // We need unique client ids to avoid looping over the same unit mesh twice (and thus overriding its original value)
    const uniqueClientIds = unitClientIds.filter((item, index) => unitClientIds.indexOf(item) === index);
    uniqueClientIds.forEach(uClientId => {
      const meshes = this.unitToMeshes[uClientId];
      if (!meshes) return;
      meshes.forEach(mesh => {
        if (!mesh.children) return;
        const unitMesh = mesh.children[0];
        unitMesh.material.opacity = HIGHLIGHTED_UNIT_OPACITY;
        unitMesh.material.color.setStyle(C.COLORS.PRIMARY);
      });
    });
  }
}
