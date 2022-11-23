import { BaseComponent, SAVED } from '../base.component';
import { ChangeDetectorRef, Component, HostListener, OnDestroy, OnInit } from '@angular/core';
import { FormArray, FormControl } from '@angular/forms';
import { hasOwnNestedProperty, shouldSave } from '../_shared-libraries/Validations';

import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../_services/api.service';
import { AreaService } from '../_services/area.service';
import { BrooksHelper } from '../_shared-libraries/BrooksHelper';
import { EditorAnalysis } from '../_shared-libraries/EditorAnalysis';
import { EditorConstants } from '../_shared-libraries/EditorConstants';
import { EditorService } from '../_services/editor.service';
import { FloorplanSplittingService } from '../_services/floorplan/floorplan.splitting.service';
import { GoogleAnalyticsService } from 'ngx-google-analytics';
import { HelpDialogSplittingComponent } from './help-splitting/help-splitting.component';
import { ImgService } from '../_services/img.service';
import { LocalStorage } from '../_shared-libraries/LocalStorage';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subscription } from 'rxjs/internal/Subscription';

const SHAFT = 'SHAFT';

// We do a m2 request by default
const REQUEST_FEATURES_ONLOAD = true;

@Component({
  selector: 'splitting-component',
  templateUrl: './splitting.component.html',
  styleUrls: ['./splitting.component.scss'],
})
export class SplittingComponent extends BaseComponent implements OnInit, OnDestroy {
  isAdmin;

  modelStructure;
  areaTypes;
  areaTypesDefined;

  selectedByDefault = null;

  /** Camera for the current layout */
  camera;

  nextApartmentId;
  selectedApartment;
  apartments;

  unitsType;

  numTotal;
  numNotDefined;

  scale;
  isScaled;

  // Display a background image in the floorplan editor
  backgroundImg;
  backgroundImgWidth;
  backgroundImgHeight;
  backgroundImgScale;
  backgroundImgRotation;
  backgroundImgShiftX;
  backgroundImgShiftY;

  // Floors
  existingFloorsIds;
  currentFloorId;

  changedApartmentSubscription: Subscription;
  activatedRoute_sub: Subscription;

  constructor(
    protected $gaService: GoogleAnalyticsService,
    public apiService: ApiService,
    public areaService: AreaService,
    public imgService: ImgService,
    public editorService: EditorService,
    public dialog: MatDialog,
    public snackBar: MatSnackBar,
    private activatedRoute: ActivatedRoute,
    public logic: FloorplanSplittingService,
    private cdr: ChangeDetectorRef
  ) {
    super();
  }

  ngOnInit(): void {
    this.$gaService.pageView('/splitting', 'Splitting tool');
    if (!this.activatedRoute_sub) {
      this.activatedRoute_sub = this.loadOnNewParameters(this.activatedRoute, () => this.loadData(), ['plan_id']);
    }

    const userRoles = LocalStorage.getApiRoles();
    this.isAdmin = userRoles?.includes('ADMIN');
  }

  /**
   * Resets to the initial values of the attributes
   */
  resetData() {
    this.contentNew();
    this.resetSplitData();
    this.modelStructure = null;
    this.resetScaleData();
  }

  resetSplitData() {
    this.loading = true;

    this.selectedByDefault = null;

    this.nextApartmentId = 1;
    this.selectedApartment = 1;
    this.apartments = [];
    this.unitsType = new FormArray([]);

    this.numTotal = 0;
    this.numNotDefined = 0;
  }

  resetScaleData() {
    this.isScaled = false;
    this.scale = 1;
  }

  async loadData() {
    try {
      this.resetData();
      await this.requestPlanData(this.apiService, this.plan_id);
      this.isScaled = this.planData?.georef_scale > 0;
      await this.getModelStructure(this.plan_id);
    } catch (e) {
      this.parseError(e);
    }
  }

  loadApartments(plan_id) {
    this.apiService
      .getApartment(plan_id)
      .then(apartments => {
        this.processLoadedPlan(apartments);
      })
      .catch(e => {
        this.loadPlanErrors(e);
      });
  }

  loadApartmentsAutoSplit(plan_id) {
    this.contentNew();
    this.resetSplitData();
    this.apiService
      .getApartmentAutoSplit(plan_id)
      .then(apartments => {
        this.processLoadedPlan(apartments);
        this.contentChanged();
      })
      .catch(e => {
        this.loadPlanErrors(e);
      });
  }

  processLoadedPlan(apartments) {
    if (apartments) {
      // Unique floors:
      this.existingFloorsIds = Array.from(new Set(apartments.map(apartment => apartment.floor_id)));

      if (this.existingFloorsIds?.length > 0) {
        this.currentFloorId = this.existingFloorsIds[0];
      } else {
        this.currentFloorId = null;
      }

      // @ts-ignore
      apartments.forEach(apartment => {
        if (this.currentFloorId === null || this.currentFloorId === apartment.floor_id) {
          // tslint:disable-next-line
          apartment = this.newApartment(apartment['apartment_no']);
          apartment.modified = true;

          if (apartment['apartment_no'] > this.nextApartmentId) {
            this.nextApartmentId = apartment['apartment_no'] + 1;
          }
        }
      });
      this.loading = false;
      this.editorService.setApartmentAreas(apartments);
    }
  }

  loadPlanErrors(e) {
    if (e.status && e.status === 404) {
      // We create one by default, nothing was found
      this.newApartment(null);
      const floorNr = EditorConstants.DEFAULT_FLOOR;
      const defaultUnit = 1;
      this.editorService.setSelectedApartment(defaultUnit, floorNr);
    } else {
      this.parseError(e);
    }
    this.loading = false;
  }

  async getModelStructure(plan_id: string) {
    this.loadApartments(plan_id);

    try {
      const siteData = await this.apiService.getSite(this.planData.site_id);
      const areaTypeStructure = await this.apiService.getClassificationScheme(siteData.classification_scheme);

      const areaData = BrooksHelper.getAreaData(areaTypeStructure);
      this.areaTypes = BrooksHelper.getAreaTypes(areaData);

      const modelStructure = await this.apiService.getBrooksById(plan_id, true);
      await this.areaService.setReferenceBrooksModel(plan_id, modelStructure);
      this.areaService.applyNewAreas(plan_id);

      await this.imgService.loadBackgroundImg(this, this.planData, this.apiService);

      this.modelStructure = modelStructure;

      this.areaTypesDefined = this.areaTypes.filter(at => at !== 'NOT_DEFINED');

      this.updateNotDefined();

      if (!this.changedApartmentSubscription) {
        this.changedApartmentSubscription = this.editorService.changedApartment.subscribe(nextChange => {
          this.reactionToChangeApartment(nextChange);
        });
      }
    } catch (e) {
      this.parseError(e);
    }
  }

  async savePlanWithoutUnits() {
    try {
      await this.apiService.updatePlanWithoutUnits(this.plan_id, this.planData?.without_units);
    } catch (e) {
      this.parseError(e);
    }
  }
  /**
   * An area has changed it's apartment (Or didn't have, and now has something)
   * @param nextChange
   */
  async reactionToChangeApartment(nextChange) {
    if (nextChange) {
      if (nextChange.manual) {
        // There has been changes, we allow the user to save
        this.contentChanged();
      }
      this.removeOldApartment(nextChange).then();
      this.addNewApartment(nextChange).then();
    }
  }

  removeAreaFromArray(array, areaId) {
    const index = array.indexOf(areaId);
    if (index >= 0) {
      array.splice(index, 1);
    }
  }

  /**
   * @param apartment
   * @param result
   */
  updateM2report(apartment, result) {
    if (apartment) {
      apartment.rooms = result['number-of-rooms'];
      apartment.ANF = result['area-sia416-ANF'];
      apartment.FF = result['area-sia416-FF'];
      apartment.HNF = result['area-sia416-HNF'];
      apartment.NNF = result['area-sia416-NNF'];
      apartment.VF = result['area-sia416-VF'];
    }
  }

  /**
   * Add to the apartments the data from the change
   * @param nextChange
   */
  async addNewApartment(nextChange) {
    const areaFound = this.areaService.getAreaInfo(nextChange.el.floorNr, nextChange.el.id);
    if (typeof nextChange.new !== 'undefined') {
      if (nextChange.new === -1 || nextChange.new === null) {
        // Public space
      } else {
        const newA = this.apartments.find(a => `${a.id}` === `${nextChange.new}`);
        if (newA) {
          newA.areasId.push(areaFound.id);
          this.updateApartmentData(nextChange, newA);

          if (nextChange.manual) {
            newA.modified = true;
          }
        }

        this.numNotDefined -= 1;
      }
    }
  }

  updateApartmentData(nextChange, newApartment) {
    // By default we don't load the metrics
    const loadedApartment = typeof nextChange.old === 'undefined';
    if (REQUEST_FEATURES_ONLOAD || !loadedApartment) {
      this.apiService.getBasicFeaturesDelayedAndGrouped(
        this.site_id,
        this.plan_id,
        nextChange.new,
        newApartment.areasId,
        (error, result) => {
          if (error) {
            this.parseError(error);
          } else {
            this.updateM2report(newApartment, result);
          }
        }
      );
    }
  }

  /**
   * Remove from the apartments the data from the change
   * @param nextChange
   */
  async removeOldApartment(nextChange) {
    const areaFound = this.areaService.getAreaInfo(nextChange.el.floorNr, nextChange.el.id);
    if (typeof nextChange.old !== 'undefined') {
      if (nextChange.old === -1 || nextChange.old === null) {
        // Public space
      } else {
        const oldA = this.apartments.find(a => `${a.id}` === `${nextChange.old}`);
        if (oldA) {
          this.removeAreaFromArray(oldA.areasId, areaFound.id);
          this.updateApartmentData(nextChange, oldA);

          if (nextChange.manual) {
            oldA.modified = true;
          }
        }
      }

      if (this.shouldIncreaseNotDefined(nextChange)) {
        this.numNotDefined += 1;
      }
    }
  }

  @HostListener('document:keydown', ['$event'])
  handleKeyDown(e) {
    // B 66
    if (e.which > 48 && e.which <= 57) {
      e.preventDefault();

      const index = e.which - 48;
      const apartment = this.apartments[index - 1];
      if (apartment) {
        this.selectApartment(apartment.id);
      }

      // Press 'N' to create a new apartment
    } else if (e.which === 78) {
      e.preventDefault();
      this.newApartment(null);

      // P selects public space
    } else if (e.which === 80) {
      e.preventDefault();
      this.selectApartment(-1);

      // Back space deletes the selected apartment
    } else if (e.which === 8) {
      e.preventDefault();
      this.removeApartment(this.selectedApartment, true);

      // Tabulator changes the selected Unit
    } else if (e.which === 9) {
      e.preventDefault();

      if (this.apartments) {
        const apartmentsIds = [-1, ...this.apartments.map(a => a.id)];
        const position = apartmentsIds.indexOf(this.selectedApartment);
        if (position !== null) {
          this.selectApartment(apartmentsIds[(position + 1) % apartmentsIds.length]);
        }
      }

      // Center with 0
    } else if (e.which === 48) {
      e.preventDefault();
      this.editorService.centerCamera(true);
    }
  }

  handleUnitTypeChange(changedIndex) {
    this.apartments.forEach((app, index) => {
      if (changedIndex === index) {
        app.modified = true;
      }
    });
    this.contentChanged();
  }

  /**
   * We removed all the apartments both in server and in front-end
   */
  removeAllApartments() {
    this.apartments.forEach(app => this.removeApartment(app.id, false));
  }

  updateNotDefined() {
    const statistics = EditorAnalysis.analyzeModelStructure(this.modelStructure, this.areaService, this.areaTypes);
    this.numTotal = 0;
    this.areaTypes
      .filter(at => at !== SHAFT)
      .forEach(at => {
        this.numTotal += statistics[at].length;
      });

    this.numNotDefined = this.numTotal;
  }

  changedCamera(currentCamera) {
    this.camera = currentCamera;
  }

  reloadModel() {
    const ms = this.modelStructure;
    this.modelStructure = null;
    setTimeout(() => {
      this.modelStructure = ms;
    }, 0);
  }

  /**
   * We mark the apartment as the active.
   * When clicking in an area would then be assigned to this apartment
   * @param apartmentId
   */
  selectApartment(apartmentId) {
    this.selectedApartment = apartmentId;
    const floorNr = EditorConstants.DEFAULT_FLOOR;
    this.editorService.setSelectedApartment(apartmentId, floorNr);
  }

  isModified(apartment) {
    return apartment.modified;
  }

  /**
   * Event when click in remove apartment.
   * Warning when the apartment has areas assigned.
   * Select another apartment if the removed one was deselected
   * @param apartmentId
   * @param showConfirmation
   */
  removeApartment(apartmentId, showConfirmation: boolean): void {
    const selected = this.apartments.find(a => `${a.id}` === `${apartmentId}`);
    selected.modified = true;

    if (
      selected &&
      (selected.m2 <= 0 || !showConfirmation || window.confirm('The apartment has areas assigned. Are you sure?'))
    ) {
      try {
        this.apiService.removeApartment(this.plan_id, apartmentId);

        const removedIndex = this.apartments.findIndex(a => `${a.id}` === `${apartmentId}`);
        this.unitsType.removeAt(removedIndex);

        this.apartments = this.apartments.filter(a => `${a.id}` !== `${apartmentId}`);

        // If there're areas associated we mark them as free and we notify the server.
        if (selected.areasId?.length > 0) {
          this.editorService.removeApartmentAreas(selected.areasId);
        }

        // We select the first apartment, if there's one
        if (this.selectedApartment === apartmentId && this.apartments.length > 0) {
          this.selectApartment(this.apartments[0].id);
        }
      } catch (e) {
        this.parseError(e);
      }
    }
  }

  /**
   * The user creates a new apartment.
   * We set up the data structure and assign an id and a color
   * @param forceApartmentId if assigned this id is used instead the autogenerated
   * @param unitType when an unit type is set is saved to be selected later
   */
  newApartment(forceApartmentId, unitType = '') {
    let apartmentId = this.nextApartmentId;
    if (forceApartmentId !== null && forceApartmentId >= 0) {
      apartmentId = forceApartmentId;
    }

    const newApartment = {
      id: apartmentId,
      areasId: [],
      color: EditorConstants.COLORS[apartmentId % EditorConstants.COLORS.length],
      m2report: {},
      rooms: 0,
      modified: false,
    };

    this.apartments.push(newApartment);
    this.unitsType.push(new FormControl(unitType));
    this.selectApartment(apartmentId);

    if (forceApartmentId >= this.nextApartmentId) {
      this.nextApartmentId = forceApartmentId + 1;
    } else {
      this.nextApartmentId += 1;
    }

    return newApartment;
  }

  /**
   * Save all the apartments
   */
  async save() {
    const newUnits = [];
    const requestDelete = [];
    this.saving = true;

    if (!(await shouldSave(this.apiService, this.plan_id))) {
      this.saving = false;
      return;
    }

    this.saveText = null;

    this.setBrooksErrorsEmpty();

    this.apartments.forEach((app, index) => {
      if (app.modified) {
        // Save if there are areas
        if (app.areasId?.length > 0) {
          newUnits.push({
            id: app.id,
            areasId: app.areasId,
            type: this.unitsType.at(index).value,
          });

          // DELETE if not
        } else {
          requestDelete.push(this.apiService.removeApartment(this.plan_id, app.id));
        }
      }
    });

    this.reactToSaveRequests(newUnits, requestDelete).then();
  }

  setBrooksErrorsEmpty() {
    const previous = this.modelStructure;
    previous.errors = [];
    this.resetBrooks(previous);
  }

  shouldIncreaseNotDefined(nextChange) {
    const isNewAreaUndefined = nextChange.new === null;
    const isNewAreaPublic = nextChange.new === -1;
    return !isNewAreaUndefined && !isNewAreaPublic;
  }

  setApartmentNotModified(apartmentId) {
    const apartment = this.apartments.find(a => `${a.id}` === `${apartmentId}`);
    if (apartment) {
      apartment.modified = false;
    }
  }

  /**
   * We wait for all the request to finish and take action based on the result
   */
  async reactToSaveRequests(newUnits, requestDelete) {
    try {
      // All the delete requests are done in parallel (No validation done)
      await Promise.all(requestDelete);

      // Save requests, we go one by one and we stop if exception
      for (let i = 0; i < newUnits.length; i += 1) {
        this.savingText = `Saving ... (${i + 1} / ${newUnits.length})`;

        const { id, areasId, type } = newUnits[i];
        await this.apiService.createApartment(this.plan_id, id, areasId, type);
        this.setApartmentNotModified(newUnits[i].id);
      }

      this.saveCompleted();
    } catch (error) {
      if (!this.parseBrooksError(error)) {
        this.parseError(error);
      }
      this.contentChanged();
      this.snackBar.open('Error saving the apartments, check the error list and the dots in the floorplan.', 'Error', {
        duration: 0,
      });
    }
  }

  saveCompleted() {
    this.saveDisabled = true;
    this.saveText = SAVED;
    this.saving = false;
    this.snackBar.open('Splitting saved successfully', 'Okay', {
      duration: 0,
    });
    this.apiService.completeSplitting();
  }

  /**
   * If the error is a collection of modelStructure errors we list & display them in the floorplan
   * @param error
   */
  parseBrooksError(error) {
    if (hasOwnNestedProperty(error, 'error.errors') && Array.isArray(error.error.errors)) {
      this.saving = false;
      const previous = this.modelStructure;
      previous.errors = error.error.errors;
      this.resetBrooks(previous);

      return true;
    }
    return false;
  }

  resetBrooks(newBrooks) {
    // This forces the model structure to reload
    this.modelStructure = null;
    setTimeout(() => {
      this.modelStructure = newBrooks;
    }, 10);
  }

  /**
   * Opens the splitting help panel
   */
  openDialog(): void {
    this.dialog.open(HelpDialogSplittingComponent, {
      id: 'helpDialog',
      minWidth: '450px',
    });
  }

  /**
   * Unsubscribe from everything when destroying the component
   */
  ngOnDestroy(): void {
    if (this.changedApartmentSubscription) {
      this.changedApartmentSubscription.unsubscribe();
    }
    if (this.activatedRoute_sub) {
      this.activatedRoute_sub.unsubscribe();
    }
  }

  /**
   * If the user leaves the page with unsaved changes we notify him.
   * @param $event
   */
  @HostListener('window:beforeunload', ['$event'])
  confirmationOfChangesNotSaved($event) {
    if (!this.saveDisabled) {
      $event.returnValue = 'There are changes that were not saved, are you sure you want to leave?';
    }
  }
}
