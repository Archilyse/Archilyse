import { ImgService } from './img.service';
/**
 * This class in a mock of the editor service for testing purposes.
 */
import { Injectable } from '@angular/core';
import { of } from 'rxjs/internal/observable/of';

@Injectable({
  providedIn: 'root',
})
export class MockImgService extends ImgService {
  constructor() {
    super();
  }

  loadBackgroundImg(component, planData, apiService) {
    return of(void 0).toPromise();
  }
}
