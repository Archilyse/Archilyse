import { Injectable } from '@angular/core';
import { ApiService } from './api.service';
import { EditorConstants, isAnArea } from '../_shared-libraries/EditorConstants';
import { Vector2 } from 'three-full/builds/Three.es';
import { FloorplanInterfaceService } from './floorplan/floorplan.interface.service';
import { BrooksHelper } from '../_shared-libraries/BrooksHelper';
import { EditorService } from './editor.service';
import { FloorplanIdManager } from './floorplan/floorplanIdManager';

@Injectable({
  providedIn: 'root',
})
export class AreaService {
  _area_cache = {};
  _area_cache_by_id = {};

  _plan_area_types = {};

  _colors = null;

  _brooks_model;
  _brooks_model_areas;

  _fallbackToBrooks = true;

  constructor(public apiService: ApiService, public editorService: EditorService) {}

  /**
   * By default we provide an error but fallback to brooks can be set to true for debug purposes.
   * @param fallbackToBrooks
   */
  setFallback(fallbackToBrooks: boolean) {
    this._fallbackToBrooks = fallbackToBrooks;
  }

  /**
   * We set the color scheme to display area types
   * @param colors
   */
  setColors(colors) {
    this._colors = colors;
  }
  getColors() {
    return this._colors;
  }

  /**
   * We tell the service what's the brooks model we're working on
   * @param planId
   * @param brooksModel
   */
  async setReferenceBrooksModel(planId: string, brooksModel, auto_classified: boolean = false) {
    // We reset the timeouts on a new Brooks
    const areaList = [];
    const initialPosition = new Vector2(0, 0);

    this.getBrooksModelAreas(areaList, initialPosition, brooksModel);

    this._brooks_model = brooksModel;
    this._brooks_model_areas = areaList;

    this._plan_area_types[planId] = await this.apiService.getPlanAreas(planId, auto_classified);
    this.applyNewAreas(planId);
    return this._plan_area_types[planId];
  }

  /**
   * Returns all the area id-area_type pairs for a given plan.
   * @param planId
   */
  getAreaTypes(planId: string) {
    return this._plan_area_types[planId].map(area => {
      return {
        id: area.id,
        area_type: area.area_type,
      };
    });
  }

  /**
   * Returns a dictionary id:area_type with all the plans for a given planId
   * @param planId
   */
  getAreaTypesDict(planId: string) {
    const areas = this.getAreaTypes(planId);
    const result = {};
    areas.forEach(area => {
      result[area.id] = area.area_type;
    });
    return result;
  }

  /**
   * Matches the planId areas to the current brooks to further querying
   * @param planId
   */
  applyNewAreas(planId: string) {
    this._plan_area_types[planId].forEach(areaType => {
      const areaFound = BrooksHelper.getAreaByPoint(this._brooks_model, [areaType.coord_x, areaType.coord_y]);
      if (areaFound) {
        let areaId = FloorplanIdManager.getAreaId(areaFound.id, EditorConstants.DEFAULT_FLOOR);
        if (Number.isInteger(areaFound.floorNr)) {
          areaId = FloorplanIdManager.getAreaId(areaFound.id, areaFound.floorNr);
        }

        this._area_cache[areaId] = areaType;
        this._area_cache_by_id[areaType.id] = areaFound;
      } else {
        console.error(areaType);
        throw new Error(`Point not found for the area ${areaType.id}. Changes in the editor have not been saved`);
      }
    });
  }

  /**
   * Gets anb array of Area Id's and returns an array of Mesh uid's
   * @param areaIds
   */
  mapAreaIdToMeshId(areaIds): string[] {
    return areaIds.map(areaId => this._area_cache_by_id[areaId].id);
  }

  /**
   * Given the floor and the areaMeshId returns the Area Db entity that matches
   * @param floorNr
   * @param areaMeshId
   */
  getAreaInfo(floorNr, areaMeshId: string) {
    let areaFoundId = FloorplanIdManager.getAreaId(areaMeshId, EditorConstants.DEFAULT_FLOOR);
    if (Number.isInteger(floorNr)) {
      areaFoundId = FloorplanIdManager.getAreaId(areaMeshId, floorNr);
    }
    return this._area_cache[areaFoundId];
  }

  /**
   * Given the Area Id from the db return the Area Mesh information
   * @param areaId
   */
  getAreaByAreaId(areaId) {
    return this._area_cache_by_id[areaId];
  }

  /**
   * Given an area Mesh element get get it's area type.
   * If not found, we return the original type of the element giving an error in the console
   * @param element
   */
  getAreaTypeByElement(element) {
    const areaType = this.getAreaInfo(element.floorNr, element.id);
    if (areaType) {
      return areaType.area_type;
    }

    if (this._fallbackToBrooks) {
      console.log('FallbackToBrooks:', element.id);
      return BrooksHelper.getHumanType(element.type);
    }

    console.error('Area not found ', element);
    throw new Error('Area not found');
  }

  /**
   * Given a floorNr and a Mesh Area id, se set the type
   * @param floorNr
   * @param areaId
   * @param type
   */
  setAreaType(floorNr, areaId: string, type: string) {
    const areaFoundId = FloorplanIdManager.getAreaId(areaId, floorNr);
    if (this._area_cache[areaFoundId]) {
      this._area_cache[areaFoundId].area_type = type;
    } else {
      console.error('Area nor found', areaId, floorNr, areaFoundId, this._area_cache);
    }
  }

  /**
   * Finds recursively the area and it's parent for the given areaId.
   * @param areaList -
   * @param position
   * @param brooksModel
   */
  getBrooksModelAreas(areaList: any[], position: number[], brooksModel) {
    if (brooksModel) {
      if (isAnArea(brooksModel.type)) {
        areaList.push({
          type: brooksModel.type,
          footprint: brooksModel.footprint,
        });
      }
      if (brooksModel.children) {
        for (let i = 0; i < brooksModel.children.length; i += 1) {
          const child = brooksModel.children[i];
          this.getBrooksModelAreas(areaList, position, child);
        }
      }
    }
  }

  findArea(areaId) {
    return this.findAreaInBrooksModel(this._brooks_model, null, areaId);
  }

  /**
   * Finds recursively the area and it's parent for the given areaId.
   * @param brooksModel
   * @param parent
   * @param areaId
   */
  findAreaInBrooksModel(brooksModel, parent, areaId) {
    if (brooksModel.id === areaId) {
      const type = brooksModel.type;
      const typeShort = BrooksHelper.getHumanType(type);

      return {
        parent,
        type: typeShort,
        parentId: parent.id,
      };
    }
    if (brooksModel.children) {
      for (let i = 0; i < brooksModel.children.length; i += 1) {
        const child = brooksModel.children[i];
        const result = this.findAreaInBrooksModel(child, brooksModel, areaId);
        if (result !== null) {
          return result;
        }
      }
    }
    return null;
  }
}
