import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs/internal/BehaviorSubject';

interface OriginalData {
  railings?;
  walls?;
}

interface PostprocessData {
  changes: OriginalData;
  loading: boolean;
}

interface PostprocessChangeData {
  change: [];
  key: string;
  name: string;
  relevant: boolean;
}

@Injectable({
  providedIn: 'root',
})
export class PostprocessService {
  private postprocessOriginalSource = new BehaviorSubject<OriginalData>(null);
  public postprocessOriginal = this.postprocessOriginalSource.asObservable();

  private postprocessSource = new BehaviorSubject<PostprocessData>(null);
  public postprocess = this.postprocessSource.asObservable();

  private postprocessPreviewSource = new BehaviorSubject<PostprocessChangeData>(null);
  public postprocessPreview = this.postprocessPreviewSource.asObservable();

  private postprocessApplySource = new BehaviorSubject<PostprocessChangeData>(null);
  public postprocessApply = this.postprocessApplySource.asObservable();

  constructor() {}

  /**
   * We make sure that the initial values when we navigate are reset
   */
  resetValuesForNavigation() {
    this.postprocessSource.next(null);
    this.postprocessOriginalSource.next(null);
    this.postprocessPreviewSource.next(null);
    this.postprocessApplySource.next(null);
  }

  setPostprocessData(changes: PostprocessData): void {
    this.postprocessSource.next(changes);
  }
  setPostprocessOriginalData(originalElements: OriginalData): void {
    this.postprocessOriginalSource.next(originalElements);
  }
  setPostprocessPreview(change: PostprocessChangeData): void {
    this.postprocessPreviewSource.next(change);
  }
  setPostprocessApply(change: PostprocessChangeData): void {
    this.postprocessApplySource.next(change);
  }
}
