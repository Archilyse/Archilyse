import { tap, timeout } from 'rxjs/operators';

import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { NavigationConstants } from '../_shared-libraries/NavigationConstants';
import { environment } from '../../environments/environment';
import { of } from 'rxjs/internal/observable/of';

const CACHE_TIME_MS = 600; // 0.6 second delay
const GET_BROOKS_TIMEOUT = 180000;

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private _timeouts = {};
  private _payloads = {};
  private _callback = {};

  public status = {
    editor: null,
    linking: null,
    splitting: null,
    classification: null,
    scaling: null,
    georeference: null,
  };

  constructor(private http: HttpClient) {}

  statusError(error) {
    console.log('Error setting app status:', error);
  }

  defaultStatus() {
    this.status.editor = NavigationConstants.APP_AVAILABLE;
    this.status.linking = NavigationConstants.APP_DISABLED;
    this.status.splitting = NavigationConstants.APP_DISABLED;
    this.status.classification = NavigationConstants.APP_DISABLED;
    this.status.georeference = NavigationConstants.APP_DISABLED;
  }
  startEdition() {
    this.defaultStatus();
  }
  completeEdition() {
    this.status.editor = NavigationConstants.APP_COMPLETED;

    // Edition unlocks classification
    if (this.status.classification !== NavigationConstants.APP_COMPLETED) {
      this.status.classification = NavigationConstants.APP_AVAILABLE;
    }
  }
  completeClassification() {
    this.status.editor = NavigationConstants.APP_COMPLETED;
    this.status.classification = NavigationConstants.APP_COMPLETED;

    if (this.status.georeference !== NavigationConstants.APP_COMPLETED) {
      this.status.georeference = NavigationConstants.APP_AVAILABLE;
    }
  }
  invalidateClassification() {
    this.status.editor = NavigationConstants.APP_COMPLETED;
    this.status.classification = NavigationConstants.APP_AVAILABLE;
    this.status.scaling = NavigationConstants.APP_DISABLED;
    this.status.georeference = NavigationConstants.APP_DISABLED;
    this.status.splitting = NavigationConstants.APP_DISABLED;
    this.status.linking = NavigationConstants.APP_DISABLED;
  }
  completeLinking() {
    // This is the final step
    this.status.linking = NavigationConstants.APP_COMPLETED;
  }

  completeGeoreferencing() {
    this.status.georeference = NavigationConstants.APP_COMPLETED;
    // Georeference unlocks splitting
    if (this.status.splitting !== NavigationConstants.APP_COMPLETED) {
      this.status.splitting = NavigationConstants.APP_AVAILABLE;
    }
  }

  completeSplitting() {
    this.status.splitting = NavigationConstants.APP_COMPLETED;

    // Splitting unlocks linking
    if (this.status.linking !== NavigationConstants.APP_COMPLETED) {
      this.status.linking = NavigationConstants.APP_AVAILABLE;
    }
  }

  /**
   * Put of a plan we update the steps that were completed
   * @param planId
   */
  async setAppStatus(planId) {
    const planStatus: any = await this.http
      .get(`${environment.apiPlanUrl}${planId}/status`)
      .toPromise()
      .catch(error => this.statusError(error));

    this.defaultStatus();

    // If planStatus failed, we don't do anything
    if (planStatus) {
      const editorCompleted = planStatus.labelled;
      const classificationCompleted = planStatus.classified;
      const georeferenceCompleted = planStatus.georeferenced;
      const splittingCompleted = planStatus.splitted;
      const linkingCompleted = planStatus.units_linked;

      // Edition
      if (editorCompleted) {
        this.completeEdition();

        // Classification
        if (classificationCompleted) {
          this.completeClassification();
        } else {
          this.completeEdition();
        }

        // Splitting
        if (splittingCompleted) {
          this.completeSplitting();
        }

        // Georeference
        if (georeferenceCompleted) {
          this.completeGeoreferencing();
        }

        // Linking
        if (linkingCompleted) {
          this.completeLinking();
        }
      }
    }
  }

  login(user: string, password: string, previousUrl: string): Promise<any> {
    return this.http
      .post(`${environment.apiAuthUrl}`, {
        user,
        password,
      })
      .toPromise();
  }

  /**
   * Get floorplan image used as background image in every step
   * @param planId
   */
  getPlanBackgroundImage(planId): Promise<any> {
    return this.http.get(`${environment.apiPlanUrl}${planId}/raw_image`, { responseType: 'blob' }).toPromise();
  }
  /**
   * Get transformations for floorplan image
   * @param planId
   */
  getPlanBackgroundImageTransformation(planId): Promise<any> {
    return this.http.get(`${environment.apiPlanUrl}${planId}/image_transformation`).toPromise();
  }

  /**
   * We get the current structure
   * @param siteId number
   */
  getSiteBuildingAndFloors(siteId: string): Promise<any> {
    return this.http.get(`${environment.apiSiteUrl}${siteId}/structure`).toPromise();
  }

  /**
   * Get's the information about an specific site
   * @param siteId
   */
  getSite(siteId: string): Promise<any> {
    return this.http.get(`${environment.apiSiteUrl}${siteId}`).toPromise();
  }

  /**
   * Get's the information about an specific site
   * @param siteId
   */
  getUnitsBySite(siteId: string): Promise<any> {
    return this.http.get(`${environment.apiSiteUrl}${siteId}/units`).toPromise();
  }

  getPlanAreas(planId: string, auto_classified: boolean): Promise<any> {
    return this.http
      .get(`${environment.apiPlanUrl}${planId}/areas${auto_classified ? '/autoclassified' : ''}`)
      .toPromise();
  }

  validateAreaTypes(planId: string, areaTypes): Promise<any> {
    return this.http
      .post(`${environment.apiPlanUrl}${planId}/areas/validate`, {
        areas: areaTypes,
      })
      .toPromise();
  }

  updateAreaTypes(planId: string, areaTypes): Promise<any> {
    return this.http
      .put(`${environment.apiPlanUrl}${planId}/areas`, {
        areas: areaTypes,
      })
      .toPromise();
  }

  /**
   * Updates the site information
   * @param id
   * @param data
   */
  updateSite(id: string, data: any): Promise<any> {
    return this.http.put(`${environment.apiSiteUrl}${id}`, data).toPromise();
  }

  /**
   * Get the areaTypes from the backend
   * @param scheme
   */
  getClassificationScheme(scheme: string): Promise<any> {
    return this.http.get(`${environment.apiConstantsUrl}classification_schemes/${scheme}`).toPromise();
  }

  /**
   * Get common area filters from backend
   * @param scheme
   */
  getAreaFilters(scheme: string): Promise<any> {
    return this.http.get(`${environment.apiConstantsUrl}classification_area_filters/${scheme}`).toPromise();
  }

  /**
   * get the current status of a simulation
   */
  getSimulationById(simulation_id): Promise<any> {
    return this.http.get(`${environment.apiPotentialUrl}${simulation_id}`).toPromise();
  }

  /**
   * Get the validated and optionally classified brooks model by ID.
   * @param planIdformatM2Price.ts
   * @param classified
   */
  getBrooksById(planId: string, classified: boolean = false): Promise<any> {
    return this.http
      .get(`${environment.apiPlanUrl}${planId}/brooks?validate=true&classified=${classified}`)
      .pipe(timeout(GET_BROOKS_TIMEOUT))
      .toPromise();
  }

  getFootprintById(planId: string): Promise<any> {
    return this.http.get(`${environment.apiPlanUrl}${planId}/georeferencing/footprint`).toPromise();
  }

  /**
   * Request the plan information from the given planId
   * @param planId
   * @param requestStatus
   */
  getPlanData(planId: string, requestStatus: boolean = true): Promise<any> {
    return this.http
      .get(`${environment.apiPlanUrl}${planId}`)
      .pipe(
        tap(plan => {
          if (requestStatus) {
            // @ts-ignore
            this.setAppStatus(plan.id);
          }
        })
      )
      .toPromise();
  }

  /**
   * Update the plan `without_units` field from the given planId
   * @param planId
   * @param requestStatus
   */
  updatePlanWithoutUnits(planId: string, without_units): Promise<any> {
    return this.http.patch(`${environment.apiPlanUrl}${planId}`, { without_units }).toPromise();
  }

  /**
   * Get the units by plan
   * @param planId
   */
  getUnitsByPlan(planId: string): Promise<any> {
    return this.http.get(`${environment.apiPlanUrl}${planId}/units`).toPromise();
  }

  /**
   * Get the pipelines of a site
   * @param siteId
   */
  getPipelinesBySite(siteId: string): Promise<any> {
    return this.http.get(`${environment.apiSiteUrl}${siteId}/pipeline`).toPromise();
  }

  /**
   * Get the floor by building ID
   * @param building_id
   */
  getFloorsByBuildingId(building_id: string): Promise<any> {
    return this.http.get(`${environment.apiFloorUrl}?building_id=${building_id}`).toPromise();
  }

  /**
   * Update units in a plan
   * @param planId
   * @param units
   */
  updateUnits(planId: string, units): Promise<any> {
    return this.http.put(`${environment.apiPlanUrl}${planId}/units`, units).toPromise();
  }

  /**
   * Gets the apartments for the given planId with their areasIds
   * @param planId
   * @param scale
   */
  updateScaleFactor(planId: string, scale: number): Promise<any> {
    return this.http.patch(`${environment.apiPlanUrl}${planId}`, { georef_scale: scale }).toPromise();
  }

  /**
   * Updates the values for georeference in the backend
   * @param planId
   * @param georef_rot_angle
   * @param georef_rot_x
   * @param georef_rot_y
   * @param georef_x
   * @param georef_y
   */
  updateGeoreference(planId: string, georef_rot_angle: number, georef_x: number, georef_y: number): Promise<any> {
    return this.http
      .put(`${environment.apiPlanUrl}${planId}/georeferencing`, {
        georef_rot_angle,
        georef_x,
        georef_y,
      })
      .toPromise();
  }

  /**
   * Gets the areaIds for all apartments using auto splitting
   * @param planId
   */
  getApartmentAutoSplit(planId: string): Promise<any> {
    return this.http.get(`${environment.apiPlanUrl}${planId}/autosplit`).toPromise();
  }

  /**
   * Gets the areasIds for the given apartment
   * @param planId
   */
  getApartment(planId: string): Promise<any> {
    return this.http.get(`${environment.apiPlanUrl}${planId}/apartment`).toPromise();
  }

  /**
   * Removes the selected apartment in the backend
   * @param planId
   * @param apartmentNo
   */
  removeApartment(planId: string, apartmentNo: string): Promise<any> {
    return this.http.delete(`${environment.apiPlanUrl}${planId}/apartment/${apartmentNo}`).toPromise();
  }

  /**
   * Creates an apartment to split the current floorplan
   * Double call with the same apartmentId would override the previous call.
   * @param planId
   * @param apartmentNo
   * @param areasIds the list of areas from the brooks that belong to this floorplan
   * @param type name of unit's type
   */
  createApartment(planId: string, apartmentNo: string, areasIds, type: string): Promise<any> {
    return this.http
      .put(`${environment.apiPlanUrl}${planId}/apartment/${apartmentNo}`, {
        area_ids: areasIds,
        unit_type: type,
      })
      .toPromise();
  }

  /**
   * Get the surrounding buildings footprints for the given site id
   * @param siteId
   */
  getSurroundingBuildingsFootprints(siteId: string): Promise<any> {
    return this.http.get(`${environment.apiSiteUrl}${siteId}/surrounding_buildings_footprints`).toPromise();
  }

  /**
   * Get the plans georeferenced of the same site given a plan id
   * @param planId
   */
  getGeoreferencedPlansUnderSameSite(planId: string): Promise<any> {
    return this.http.get(`${environment.apiPlanUrl}${planId}/georeferencing/footprints_site`).toPromise();
  }

  getGeoreferenceValidation(planId: string): Promise<any> {
    return this.http.get(`${environment.apiPlanUrl}${planId}/georeferencing/validate`).toPromise();
  }
  /**
   * Get's que site qa data from the client to compare with the current data
   * @param siteId
   */
  getSiteQa(siteId: string): Promise<any> {
    return this.http.get(`${environment.apiQaUrl}?site_id=${siteId}`).toPromise();
  }

  /**
   * Run basic features of a site
   * @param siteId
   */
  runBasicFeatures(siteId: string): Promise<any> {
    return this.http.post(`${environment.apiSiteUrl}${siteId}/qa-task`, {}).toPromise();
  }

  /**
   * Retrieves number of rooms, HNF, ANF and FF for the given list of area ids.
   * @param siteId
   * @param planId
   * @param areaIds
   * @param scaled
   */
  getBasicFeatures(siteId: string, planId: string, areaIds, scaled = true): Promise<any> {
    if (areaIds?.length) {
      return this.http
        .post(`${environment.apiFeaturesUrl}${siteId}/${planId}/basic?scaled=${scaled}`, { areas_ids: areaIds })
        .toPromise();
    }
    return of({
      'area-sia416-ANF': 0,
      'area-sia416-FF': 0,
      'area-sia416-HNF': 0,
      'area-sia416-NNF': 0,
      'area-sia416-VF': 0,
      'net-area': 0,
      'net-area-no-corridors': 0,
      'net-area-no-corridors-reduced-loggias': 0,
      'net-area-reduced-loggias': 0,
      'number-of-rooms': 0,
    }).toPromise();
  }

  /**
   * Request to basic features would be grouped and sent together.
   * Same unit data, would be overrided and send all the units request from the same plan at the same time.
   * We'll store the callback for each request to return to the right function for each payload
   * @param siteId
   * @param planId
   * @param unitId
   * @param areaIds
   * @param callback
   */
  getBasicFeaturesDelayedAndGrouped(siteId, planId, unitId, areaIds, callback) {
    // We store the last request
    this._payloads[unitId] = areaIds;
    this._callback[unitId] = callback;

    if (this._timeouts[planId]) {
      clearTimeout(this._timeouts[planId]);
      delete this._timeouts[planId];
    }
    this._timeouts[planId] = setTimeout(async () => {
      const unitIds = Object.keys(this._payloads);

      const payloads = unitIds.map(unitId => this._payloads[unitId]);
      const callbacks = unitIds.map(unitId => this._callback[unitId]);

      this._payloads = {};
      this._callback = {};
      try {
        const results = await this.getBasicFeatures(siteId, planId, payloads);
        if (results) {
          results.forEach((result, i) => {
            const callback = callbacks[i];
            callback(null, result);
          });
        }
      } catch (error) {
        callback(error);
      }
    }, CACHE_TIME_MS);
  }

  getAutomaticLinking(floorId: string): Promise<any> {
    return this.http.get(`${environment.apiFloorUrl}${floorId}/autolinking`).toPromise();
  }

  runSampleSurroundings(siteId: string): Promise<any> {
    return this.http.post(`${environment.apiSiteUrl}${siteId}/surroundings_sample`, {}).toPromise();
  }

  downloadSampleSurroundings(siteId: string): Promise<any> {
    return this.http
      .get(`${environment.apiSiteUrl}${siteId}/surroundings_sample`, { responseType: 'blob' })
      .toPromise();
  }
}
