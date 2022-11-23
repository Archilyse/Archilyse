import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs/internal/BehaviorSubject';
import { EditorConstants } from '../_shared-libraries/EditorConstants';

interface SelectedApartment {
  apartment;
  floorNr: number;
}

interface ChangedApartment {
  floorId;
  el; // Element that changed
  old; // Old value
  new; // New value
  manual: boolean; // Manual change or not
  areaId;
}

interface ChangedArea {
  el; // Element that changed
  old; // Old value
  new; // New value
}

interface BrooksError {
  index;
  error;
}

@Injectable({
  providedIn: 'root',
})
export class EditorService {
  private updateJSONSource = new BehaviorSubject<any>(null);
  public updateJSON = this.updateJSONSource.asObservable();

  private validatingSource = new BehaviorSubject<boolean | Error>(false);
  public validating = this.validatingSource.asObservable();

  private nextScaleSource = new BehaviorSubject<number>(0);
  public nextScale = this.nextScaleSource.asObservable();

  public nextCreateModeSource = new BehaviorSubject<any>(null);
  public nextCreateMode = this.nextCreateModeSource.asObservable();

  public nextSelectedAreaSource = new BehaviorSubject<string>(null);
  public nextSelectedArea = this.nextSelectedAreaSource.asObservable();

  public changeAngleSource = new BehaviorSubject<number>(0);
  public changeAngle = this.changeAngleSource.asObservable();

  public nextSelectedApartmentSource = new BehaviorSubject<SelectedApartment>(null);
  public nextSelectedApartment = this.nextSelectedApartmentSource.asObservable();

  public changedAreaSource = new BehaviorSubject<ChangedArea>(null);
  public changedArea = this.changedAreaSource.asObservable();

  public highlightErrorSource = new BehaviorSubject<BrooksError>(null);
  public highlightError = this.highlightErrorSource.asObservable();

  public oldClassificationSource = new BehaviorSubject<any>(null);
  public oldClassification = this.oldClassificationSource.asObservable();

  public changedApartmentSource = new BehaviorSubject<ChangedApartment>(null);
  public changedApartment = this.changedApartmentSource.asObservable();

  public getApartmentAreasSource = new BehaviorSubject<any[]>(null);
  public getApartmentAreas = this.getApartmentAreasSource.asObservable();

  public removedApartmentAreasSource = new BehaviorSubject<any[]>(null);
  public removedApartmentAreas = this.removedApartmentAreasSource.asObservable();

  private nextCenterCameraSource = new BehaviorSubject<boolean>(false);
  public nextCenterCamera = this.nextCenterCameraSource.asObservable();

  private viewFloorplanSource = new BehaviorSubject<boolean>(true);
  public viewFloorplan = this.viewFloorplanSource.asObservable();

  constructor() {}

  /**
   * We make sure that the initial values when we navigate are reset
   */
  resetValuesForNavigation() {
    this.validatingSource.next(false);
    this.updateJSONSource.next(null);
    this.nextScaleSource.next(0);
    this.nextCreateModeSource.next(null);
    this.nextSelectedAreaSource.next(null);
    this.nextSelectedApartmentSource.next(null);
    this.changedAreaSource.next(null);
    this.oldClassificationSource.next(null);
    this.changedApartmentSource.next(null);
    this.getApartmentAreasSource.next(null);
    this.removedApartmentAreasSource.next(null);
    this.nextCenterCameraSource.next(false);
    this.viewFloorplanSource.next(true);
    this.changeAngleSource.next(0);
  }

  toggleFloorplanVisibility(center: boolean) {
    this.viewFloorplanSource.next(center);
  }

  recoverClassification(oldData: any): void {
    this.oldClassificationSource.next(oldData);
  }

  updateJson(): void {
    this.updateJSONSource.next(true);
  }

  public getApartmentColor(apartmentNumber) {
    return EditorConstants.COLORS[apartmentNumber % EditorConstants.COLORS.length];
  }

  centerCamera(center: boolean) {
    this.nextCenterCameraSource.next(center);
  }

  setScale(newScale: number) {
    this.nextScaleSource.next(newScale);
  }

  setCreateMode(createMode: any) {
    this.nextCreateModeSource.next(createMode);
  }

  setSelectedArea(selectedArea: string) {
    this.nextSelectedAreaSource.next(selectedArea);
  }

  setSelectedApartment(apartment, floorNr: number) {
    this.nextSelectedApartmentSource.next(<SelectedApartment>{
      apartment,
      floorNr,
    });
  }

  setAngle(angle: number) {
    this.changeAngleSource.next(angle);
  }

  setApartmentAreas(newVals: any[]) {
    this.getApartmentAreasSource.next(newVals);
  }
  removeApartmentAreas(newVals: any[]) {
    this.removedApartmentAreasSource.next(newVals);
  }

  changedApartmentNr(element: any, oldApartment: any, newApartment: number, manualChanged: boolean, floorId, areaId) {
    this.changedApartmentSource.next(<ChangedApartment>{
      areaId,
      floorId,
      el: element,
      old: oldApartment,
      new: newApartment,
      manual: manualChanged,
    });
  }

  changedType(element: any, oldType: any, newType: string) {
    this.changedAreaSource.next(<ChangedArea>{
      el: element,
      old: oldType,
      new: newType,
    });
  }

  highlightErrorFloorplan(index: any, error: any) {
    this.highlightErrorSource.next(<BrooksError>{
      index,
      error,
    });
  }
}
