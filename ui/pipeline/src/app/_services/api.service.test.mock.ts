import { Injectable } from '@angular/core';
import { of } from 'rxjs/internal/observable/of';

import * as footprint from '../_shared-assets/http_request_brooks_footprint.json';
import * as plan from '../_shared-assets/http_request_plan.json';
import * as surroundings from '../_shared-assets/http_request_site_surrounding_footprints.json';
import * as plansgeoreferenced from '../_shared-assets/http_request_plans_georeferenced.json';
import * as site from '../_shared-assets/http_request_site.json';
import { defaultOrBase, MockApiService } from './api.service.mock';

/**
 * This class makes testing easier
 */
@Injectable({
  providedIn: 'root',
})
export class MockTestApiService extends MockApiService {
  getSite(site_id: string): Promise<any> {
    return of(defaultOrBase(site)).toPromise();
  }

  getPlanData(plan_id: string): Promise<any> {
    return of(defaultOrBase(plan)).toPromise();
  }

  getSurroundingBuildingsFootprints(siteId: string): Promise<any> {
    return of(defaultOrBase(surroundings)).toPromise();
  }

  getGeoreferencedPlansUnderSameSite(planId: string): Promise<any> {
    return of(defaultOrBase(plansgeoreferenced)).toPromise();
  }

  getFootprintById(plan_id: string): Promise<any> {
    return of(defaultOrBase(footprint)).toPromise();
  }

  updateGeoreference(plan_id: string, georef_rot_angle: number, georef_x: number, georef_y: number): Promise<any> {
    return of({}).toPromise();
  }
}
