import { Injectable, NgZone } from '@angular/core';
import { getAuthToken } from '../_services/auth.interceptor';
import { EventSourcePolyfill } from 'event-source-polyfill';
import { Observable } from 'rxjs/internal/Observable';
import { Observer } from 'rxjs/internal/types';
import { environment } from '../../environments/environment';
import { EventStreamApiService } from './eventstreamapi.service';

@Injectable({
  providedIn: 'root',
})
export class MockEventStreamApiService extends EventStreamApiService {
  /**
   * Get the plans georeferenced of the same site given a plan id
   * @param planId
   */
  getGeoreferencedPlansUnderSameSite(planId: string): Observable<any> {
    return new Observable<object>();
  }
}
