import { Injectable, NgZone } from '@angular/core';
import { getAuthToken } from '../_services/auth.interceptor';
import { EventSourcePolyfill } from 'event-source-polyfill';
import { Observable } from 'rxjs/internal/Observable';
import { Observer } from 'rxjs/internal/types';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class SseService {
  /**
   * Service for server-sent events (SSE), the server can terminate the
   * connection by sending a `close` event.
   */
  constructor(private _zone: NgZone) {}

  getServerSentEvent(url: string): Observable<any> {
    return new Observable((observer: Observer<object>) => {
      const eventSource = this.getEventSource(url);

      eventSource.onmessage = event => {
        this._zone.run(() => {
          if (event.data === 'close') {
            observer.complete();
            eventSource.close();
          } else {
            observer.next(event);
          }
        });
      };

      eventSource.onerror = error => {
        this._zone.run(() => {
          observer.error(error);
          eventSource.close();
        });
      };
    });
  }

  private getEventSource(url: string): EventSource {
    return new EventSourcePolyfill(url, {
      headers: {
        Authorization: `Bearer ${getAuthToken()}`,
        'Content-Type': 'text/event-stream',
        Connection: 'keep-alive',
      },
    });
  }
}

@Injectable({
  providedIn: 'root',
})
export class EventStreamApiService {
  constructor(private sseService: SseService) {}

  /**
   * Get the plans georeferenced of the same site given a plan id
   * @param planId
   */
  getGeoreferencedPlansUnderSameSite(planId: string): Observable<any> {
    return this.sseService.getServerSentEvent(
      `${environment.apiPlanUrl}${planId}/georeferencing/footprints_site/eventstream`
    );
  }
}
