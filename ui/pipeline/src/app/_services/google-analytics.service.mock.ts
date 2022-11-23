import { Injectable } from '@angular/core';

/**
 * This class in a mock of the google analytics service for unit testing purposes.
 */
@Injectable({
  providedIn: 'root',
})
export class MockGoogleAnalyticsService {
  constructor() {}

  /**
   * We don't communicate nothing to google in the unit tests
   * @param path
   * @param title
   * @param location
   * @param options
   */
  public pageView(path?: string, title?: string, location?: string, options?: Object): void {}
}
