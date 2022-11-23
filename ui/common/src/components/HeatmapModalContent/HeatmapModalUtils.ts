import { BuildingWithFloors, Unit } from '../../types';
import { FloorWithId } from './useHeatmaps';
import { HeatmapsSelectedFilters } from '.';

class HeatmapModalUtils {
  static filterFloorsByBuilding = (floors: FloorWithId[], buildingId: number): FloorWithId[] =>
    floors.filter(floor => floor.building_id === buildingId);

  static filterUnitsByFloor = (units: Unit[], floorId: number): Unit[] =>
    units.filter(unit => unit.floor_id === floorId);

  static findPositiveFloorId = (floors: FloorWithId[]): number => floors.find(floor => floor.floor_number > -1)?.id;

  static findBuildingByFloorId = (buildings: BuildingWithFloors[], floorId: number): BuildingWithFloors =>
    buildings.find(building => building.floors[floorId] !== undefined);

  static findFloorByBuildingAndFloorId = (floors: FloorWithId[], buildingId: number, floorId: number): FloorWithId => {
    const filteredFloors = HeatmapModalUtils.filterFloorsByBuilding(floors, buildingId);

    const floor = filteredFloors.find(floor => floor.id === floorId);

    return floor || null;
  };

  static findUnitIdsBySelected = (units: Unit[], selected: HeatmapsSelectedFilters): number[] => {
    let unitIds = HeatmapModalUtils.filterUnitsByFloor(units, selected.floor).map(unit => unit.id);

    if (selected.unit) unitIds = unitIds.filter(unitId => unitId === selected.unit);

    return unitIds;
  };
}

export default HeatmapModalUtils;
