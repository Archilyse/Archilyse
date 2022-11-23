import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs/internal/BehaviorSubject';
import { EditorConstants } from '../_shared-libraries/EditorConstants';

interface ScalingData {
  mode;
  pointA;
  pointB;
  polygon;
}

@Injectable({
  providedIn: 'root',
})
export class UiService {
  private scalingSource = new BehaviorSubject<boolean>(false);
  public scaling = this.scalingSource.asObservable();

  public scalingDataSource = new BehaviorSubject<ScalingData>(null);
  public scalingData = this.scalingDataSource.asObservable();

  private clickedCoordinatesSource = new BehaviorSubject<{}>(null);
  public clickedCoordinates = this.clickedCoordinatesSource.asObservable();

  private selectedClusterSource = new BehaviorSubject<{}>(null);
  public selectedCluster = this.selectedClusterSource.asObservable();

  private featuresSource = new BehaviorSubject<string[]>([]);
  public features = this.featuresSource.asObservable();

  private validateDataSource = new BehaviorSubject<boolean>(null);
  public validateData = this.validateDataSource.asObservable();

  private clickedFeatureSource = new BehaviorSubject<string>('');
  public clickedFeature = this.clickedFeatureSource.asObservable();

  private currentSelectionSource = new BehaviorSubject<Object[]>([]);
  public currentSelection = this.currentSelectionSource.asObservable();

  private dragFeatureSource = new BehaviorSubject<string>(null);
  public dragFeature = this.dragFeatureSource.asObservable();

  /**
   * We make sure that the initial values when we navigate are reset
   */
  resetValuesForNavigation() {
    this.scalingSource.next(false);
    this.scalingDataSource.next(null);
    this.clickedCoordinatesSource.next(null);
    this.featuresSource.next([]);
    this.validateDataSource.next(null);
    this.clickedFeatureSource.next('');
    this.currentSelectionSource.next([]);
    this.dragFeatureSource.next(null);
  }

  setScalingMode(scalingMode) {
    if (scalingMode) {
      this.setScalingData({
        mode: EditorConstants.SCALE_LINE,
        pointA: null,
        pointB: null,
      });
    } else {
      this.setScalingData(null);
    }
    this.scalingSource.next(scalingMode);
  }

  setScalingData(scalingData) {
    this.scalingDataSource.next(scalingData);
  }

  setClickedCoordinates(clickedXY) {
    this.clickedCoordinatesSource.next(clickedXY);
  }

  setSelectedCluster(clusterSelection) {
    this.selectedClusterSource.next(clusterSelection);
  }

  triggerValidateData() {
    this.validateDataSource.next(true);
  }

  updateFeatures(features: string[]) {
    this.featuresSource.next(features);
  }

  updateClickedFeature(feature: string) {
    this.clickedFeatureSource.next(feature);
  }

  updateCurrentSelection(currentSelection: Object[]) {
    this.currentSelectionSource.next(currentSelection);
  }

  updateDragFeatureSource(feature: string) {
    this.dragFeatureSource.next(feature);
  }
}
