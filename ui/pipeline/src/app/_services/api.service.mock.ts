import { Injectable } from '@angular/core';
import { of } from 'rxjs/internal/observable/of';
import { ApiService } from './api.service';

import * as simpleBrooks from '../_shared-assets/http_request_simpleBrooks.json';
import * as areaTypes from '../_shared-assets/http_request_areaTypes.json';
import * as apartment from '../_shared-assets/http_request_apartment.json';
import * as simData from '../_shared-assets/simData.json';
import * as site from '../_shared-assets/http_request_site.json';
import * as siteBuildingsFloors from '../_shared-assets/siteBuildingsFloors.json';
import * as siteExpectedQa from '../_shared-assets/http_request_site_expected_qa.json';
import * as buildingFloors from '../_shared-assets/http_request_building_floors.json';

export function defaultOrBase(data) {
  const defaultData = data['default'];
  return defaultData ? defaultData : data;
}

/**
 * This class in a mock of the editor service for testing purposes.
 */
@Injectable({
  providedIn: 'root',
})
export class MockApiService extends ApiService {
  constructor() {
    super(null);
  }

  login(user: string, password: string): Promise<any> {
    return of({
      msg: `Logged in as ${user}`,
      access_token: 'access_token',
    }).toPromise();
  }

  getSite(site_id: string): Promise<any> {
    return of(defaultOrBase(site)).toPromise();
  }
  getUnitsBySite(site_id: string): Promise<any> {
    return of([]).toPromise();
  }
  getPlanBackgroundImage(planId): Promise<any> {
    return of(null).toPromise();
  }
  /**
   * We get the current structure
   */
  getSiteBuildingAndFloors(siteId): Promise<any> {
    return of(defaultOrBase(siteBuildingsFloors)).toPromise();
  }
  getFloorsByBuildingId(building_id: string): Promise<any> {
    return of(defaultOrBase(buildingFloors)).toPromise();
  }

  getPlanAreas(planId: string): Promise<any> {
    return of([
      {
        area_type: 'KITCHEN_DINING',
        coord_x: 775,
        coord_y: -615,
        id: 111,
        plan_id: 1,
        units: [56899],
      },
    ]).toPromise();
  }

  updateUnits(plan_id: string, units: any): Promise<any> {
    return of(true).toPromise();
  }

  getClassificationScheme(): Promise<any> {
    return of(defaultOrBase(areaTypes)).toPromise();
  }

  getFootprintById(plan_id: string): Promise<any> {
    return of({
      coordinates: [
        [
          [394.0985414559084, -543.3157235071354],
          [418.4382405538193, -543.3157235071354],
          [394.09795106223015, -476.27314994438314],
          [394.0985414559084, -543.3157235071354],
        ],
      ],
      type: 'Polygon',
    }).toPromise();
  }

  /**
   * get the current status of a simulation
   */
  getSimulationById(simulation_id): Promise<any> {
    return of(defaultOrBase(simData)).toPromise();
  }

  getBrooksById(plan_id: string, classified: boolean): Promise<any> {
    return of(defaultOrBase(simpleBrooks)).toPromise();
  }

  getPlanData(plan_id: string): Promise<any> {
    return of({
      georef_rot_angle: -58.6886562803463,
      georef_rot_x: 2736074.27003256,
      georef_rot_y: 1196128.65027057,
      georef_scale: 0.00806756093765156,
      georef_x: 2735712.4842434,
      georef_y: 1196533.80713163,
      site_id: 1,
    }).toPromise();
  }

  updateScaleFactor(plan_id: string, scale: number): Promise<any> {
    return of(true).toPromise();
  }

  getApartment(id: string): Promise<any> {
    return of(defaultOrBase(apartment)).toPromise();
  }

  removeApartment(id: string, apartmentNo: string): Promise<any> {
    return of(true).toPromise();
  }
  createApartment(id: string, apartmentNo: string, areasIds): Promise<any> {
    return of(true).toPromise();
  }

  getGeoreferencedPlansUnderSameSite(planId: string): Promise<any> {
    return of({
      data: [
        {
          footprint: {
            coordinates: [
              [
                [2637696.097123396, 1237003.0089213396],
                [2637694.317613228, 1237006.46910652],
                [2637694.4166749856, 1237006.5200521762],
                [2637694.425244188, 1237006.5033897103],
                [2637696.35320778, 1237007.282337564],
                [2637696.332249426, 1237007.3342113108],
                [2637696.8066635435, 1237007.5258870563],
                [2637696.808161742, 1237007.5221788846],
                [2637705.6727097156, 1237011.103688746],
                [2637705.673656952, 1237011.1013442532],
                [2637705.9188166475, 1237011.2003951995],
                [2637707.5531588127, 1237007.1552563917],
                [2637707.5476542218, 1237007.1530323925],
                [2637708.2990119946, 1237005.2933566472],
                [2637708.223643355, 1237005.2629057402],
                [2637708.516824372, 1237004.5372572595],
                [2637708.5551624503, 1237004.5527468484],
                [2637709.43222397, 1237002.3819434112],
                [2637709.4673679075, 1237002.3961424837],
                [2637712.552372786, 1236994.7604874654],
                [2637712.0602686508, 1236994.5616644889],
                [2637712.057501554, 1236994.5685132935],
                [2637703.2065271563, 1236990.9924875125],
                [2637703.2040750366, 1236990.9985567222],
                [2637702.7606281745, 1236990.81939256],
                [2637702.7704535774, 1236990.7950738342],
                [2637701.0303779542, 1236990.0920376475],
                [2637701.0363007877, 1236990.0773781205],
                [2637700.9313574675, 1236990.034978267],
                [2637699.33740403, 1236993.9801514654],
                [2637699.3408700395, 1236993.9815518241],
                [2637699.325538322, 1236994.0194991566],
                [2637701.0322094085, 1236994.7090390346],
                [2637697.5029581897, 1237003.4539838303],
                [2637696.128519887, 1237002.8986747102],
                [2637696.0858221427, 1237003.0043553368],
                [2637696.097123396, 1237003.0089213396],
              ],
            ],
            type: 'Polygon',
          },
          id: 1697,
        },
      ],
    }).toPromise();
  }

  getSurroundingBuildingsFootprints(siteId: string): Promise<any> {
    return of({
      data: [
        {
          coordinates: [
            [
              [
                [2736072.155164241, 1196110.4019614581],
                [2736074.052409998, 1196130.2391100014],
                [2736080.436590002, 1196129.6179300004],
                [2736078.520890001, 1196109.7815599989],
                [2736072.8349443153, 1196110.335710324],
                [2736072.1367100016, 1196110.212550002],
                [2736072.155164241, 1196110.4019614581],
              ],
            ],
          ],
          type: 'MultiPolygon',
        },
      ],
    }).toPromise();
  }

  getSiteQa(site_id: string): Promise<any> {
    return of(defaultOrBase(siteExpectedQa)).toPromise();
  }

  getNumberOfRooms(areaStructure): Promise<any> {
    return of(areaStructure.length).toPromise();
  }
}
