import { BaseComponent, SAVE, SAVED, SAVING } from '../base.component';
import { Component, OnDestroy, OnInit, ViewChildren } from '@angular/core';
import { hasOwnNestedProperty, shouldSave } from '../_shared-libraries/Validations';

import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../_services/api.service';
import { AreaService } from '../_services/area.service';
import { EditorConstants } from '../_shared-libraries/EditorConstants';
import { EditorService } from '../_services/editor.service';
import { FloorplanLinkingService } from '../_services/floorplan/floorplan.linking.service';
import { GoogleAnalyticsService } from 'ngx-google-analytics';
import { HelpDialogLinkingComponent } from './help-linking/help-linking.component';
import { ImgService } from '../_services/img.service';
import { LocalStorage } from '../_shared-libraries/LocalStorage';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subscription } from 'rxjs/internal/Subscription';
import { floorToHumanStr } from '../_shared-libraries/FloorFormat';
import { parseErrorObj } from '../_shared-libraries/Url';

const HELP_DIALOG_MIN_WIDTH = '450px';

@Component({
  selector: 'linking-component',
  templateUrl: 'linking.component.html',
  styleUrls: ['./linking.component.scss'],
})
export class LinkingComponent extends BaseComponent implements OnInit, OnDestroy {
  @ViewChildren('input') clientInputs;

  isAdmin: boolean;
  units: any = {};

  modelStructure: any;
  selectedUnit: number;

  unitsArray: any;
  floors: any[] = [];
  loadingAutomaticLinking = false;
  visibleUnits: any[];
  scale: number;

  CLIENT_ID_REGEXP = '^[^/]+$';

  /** Camera for the current layout */
  camera: any;

  // Display a background image in the floorplan editor
  backgroundImg;
  backgroundImgWidth;
  backgroundImgHeight;
  backgroundImgScale;
  backgroundImgRotation;
  backgroundImgShiftX;
  backgroundImgShiftY;

  activatedRoute_sub: Subscription;
  changedApartmentSubscription: Subscription;
  nextSelectedApartmentSubscription: Subscription;

  constructor(
    protected $gaService: GoogleAnalyticsService,
    public apiService: ApiService,
    public areaService: AreaService,
    public imgService: ImgService,
    private activatedRoute: ActivatedRoute,
    public editorService: EditorService,
    public snackBar: MatSnackBar,
    public dialog: MatDialog,
    public logic: FloorplanLinkingService
  ) {
    super();
  }

  ngOnInit(): void {
    this.$gaService.pageView('/linking', 'Unit linking tool');
    if (!this.activatedRoute_sub) {
      const expectedParameters = ['plan_id'];
      this.activatedRoute_sub = this.loadOnNewParameters(
        this.activatedRoute,
        () => this.loadData(),
        expectedParameters
      );
    }
    const userRoles = LocalStorage.getApiRoles();
    this.isAdmin = userRoles?.includes('ADMIN');
  }

  resetData() {
    this.contentNew();
    this.loading = true;
    this.units = {};

    this.floors = [];

    this.visibleUnits = null;
    this.modelStructure = null;
  }

  async loadData() {
    this.resetData();

    try {
      this.modelStructure = await this.apiService.getBrooksById(this.plan_id, true);
      await this.areaService.setReferenceBrooksModel(this.plan_id, this.modelStructure);
      this.areaService.applyNewAreas(this.plan_id);
      await this.requestPlanData(this.apiService, this.plan_id);
      await this.imgService.loadBackgroundImg(this, this.planData, this.apiService);
      this.units = await this.loadUnits();
      this.floors = await this.getFloorIdAndNumbers(this.plan_id);

      this.unitsArray = Object.values(this.units).reduce(
        (accum: any, unitsInAFloor) => [...accum, ...Object.values(unitsInAFloor)],
        []
      );
      this.editorService.setApartmentAreas(this.visibleUnits);

      const defaultFloorId = this.floors[0] && this.floors[0].id;
      this.showFloor(defaultFloorId || 0);

      this.subscribeToApartmentChanges();
    } catch (error) {
      this.parseError(error);
    }

    this.loading = false;
  }

  subscribeToApartmentChanges() {
    if (!this.changedApartmentSubscription) {
      this.changedApartmentSubscription = this.editorService.changedApartmentSource.subscribe(unit => {
        this.parseUnit(unit);
      });
    }

    if (!this.nextSelectedApartmentSubscription) {
      this.nextSelectedApartmentSubscription = this.editorService.nextSelectedApartment.subscribe(unitData => {
        if (unitData) {
          const apartment = unitData.apartment;
          this.selectedUnit = apartment;
          this.selectInput(apartment);
        }
      });
    }
  }

  /**
   * We get the floors for the given plan Id
   */
  async getFloorIdAndNumbers(plan_id) {
    const planData = await this.apiService.getPlanData(plan_id);
    const { building_id } = planData;
    const floors = await this.apiService.getFloorsByBuildingId(building_id);
    return floors
      .filter(floor => String(floor.plan_id) === String(plan_id))
      .map(floor => ({ id: floor.id, number: floor.floor_number }));
  }

  onClientIdChange(unitNumber) {
    const floorNr = EditorConstants.DEFAULT_FLOOR;
    this.editorService.setSelectedApartment(unitNumber, floorNr);
  }
  onInputChange(event, validation) {
    const { value } = event.target;
    const hasErrors = validation && validation.errors && Object.keys(validation.errors).length > 0;
    if (value && !hasErrors) {
      this.saveDisabled = false;
      this.saveText = SAVE;
    } else {
      this.saveDisabled = true;
    }
  }

  changedCamera(currentCamera) {
    this.camera = currentCamera;
  }

  selectInput(unitNumber) {
    try {
      if (this.clientInputs) {
        const inputSelected = this.clientInputs._results.find(
          input => String(input.nativeElement.id) === String(unitNumber)
        );
        if (inputSelected) {
          inputSelected.nativeElement.focus();
          inputSelected.nativeElement.select();
        }
      }
    } catch (e) {
      // Avoid the Sentry exception:
      // 'querySelector' on 'Document': '#1' is not a valid selector.
      this.parseError(e);
    }
  }

  selectUnit(unitNumber) {
    this.selectedUnit = unitNumber;
    this.selectInput(unitNumber);
    const floorNr = EditorConstants.DEFAULT_FLOOR;
    this.editorService.setSelectedApartment(this.selectedUnit, floorNr);
  }

  parseError(e, message = '') {
    this.error = message || parseErrorObj(e);
    this.snackBar.open(this.error, 'Error', { duration: 0 });
  }

  onChangeFloor(event) {
    const selectedFloorId = event.target.value;
    this.showFloor(selectedFloorId);
  }

  async loadUnits() {
    const units = await this.apiService.getUnitsByPlan(this.plan_id).catch(this.parseError);
    if (!units || units.length <= 0) {
      const message = 'No units found, please review the Splitting';
      this.parseError(message);
      return {};
    }

    return units.reduce((accum, unit: any) => {
      accum[unit.floor_id] = accum[unit.floor_id] || {};
      accum[unit.floor_id][unit.apartment_no] = unit;
      return accum;
    }, {});
  }

  showFloor(floorId) {
    this.visibleUnits = this.unitsArray.filter((unit: any) => String(unit.floor_id) === String(floorId));
    this.editorService.setApartmentAreas(this.visibleUnits);
  }

  parseUnit(unit) {
    if (unit) {
      const { floorId, new: unitNumber } = unit;
      if (this.units?.[floorId]?.[unitNumber]) {
        const unitStats = this.units[floorId][unitNumber];
        this.updateUnitStats(unitStats, unit.el, unitNumber);
      }
    }
  }

  /**
   * We calculate the surface, number of rooms if it's a HNF surface and we update the unit statistics list.
   * @param unitStats
   * @param element
   * @param unitNumber
   */
  updateUnitStats(unitStats, element, unitNumber) {
    this.apiService.getBasicFeaturesDelayedAndGrouped(
      this.site_id,
      this.plan_id,
      unitStats.id,
      unitStats.area_ids,
      (error, basicFeatures) => {
        if (error) {
          this.parseError(error);
        } else {
          unitStats.m2 = basicFeatures['area-sia416-HNF'] + basicFeatures['area-sia416-NNF'];
          unitStats.rooms = basicFeatures['number-of-rooms'];
          unitStats.color = this.editorService.getApartmentColor(unitNumber);
        }
      }
    );
  }

  openHelpDialog(): void {
    this.dialog.open(HelpDialogLinkingComponent, {
      id: 'helpDialog',
      minWidth: HELP_DIALOG_MIN_WIDTH,
    });
  }

  async linkAutomatically() {
    const { floor_id: floorId } = this.visibleUnits[0];
    try {
      this.loadingAutomaticLinking = true;
      const linkingResult = await this.apiService.getAutomaticLinking(floorId);
      if (!linkingResult || !linkingResult.length) {
        this.snackBar.open(`Automatic linking could not be applied with the current floor & QA data`, 'Okay', {
          duration: 0,
        });
        return;
      }
      this.loadingAutomaticLinking = false;
      for (const unit of this.visibleUnits) {
        const linkedUnit = linkingResult.find(linkedUnit => linkedUnit.unit_id === unit.id);
        if (linkedUnit) {
          unit.client_id = linkedUnit.unit_client_id;
        }
      }
      this.editorService.setApartmentAreas(this.visibleUnits);
      this.snackBar.open(
        `Successfully linked automatically ${linkingResult.length} ${linkingResult.length > 1 ? 'units' : 'unit'}`,
        'Okay',
        { duration: 0 }
      );
      this.saveDisabled = false;
    } catch (error) {
      this.loadingAutomaticLinking = false;
      console.log('Error on automatic linking:', error);
    }
  }

  async onSave() {
    this.saving = true;
    this.saveDisabled = true;

    if (!(await shouldSave(this.apiService, this.plan_id))) {
      this.loading = false;
      this.saveDisabled = false;
      return;
    }

    this.saveText = SAVING;
    const allUnits = Object.values(this.units).reduce((accum: any, unitsInAFloor) => {
      const parsedUnits = Object.values(unitsInAFloor).map(unit => {
        return {
          id: unit.id,
          // When sending null BE fails
          client_id: unit.client_id ? unit.client_id.trim() : '',
          unit_usage: unit.unit_usage,
        };
      });
      return [...accum, ...parsedUnits];
    }, []);
    try {
      await this.apiService.updateUnits(this.plan_id, allUnits);
      this.saveText = SAVED;
      this.snackBar.open('Linking saved successfully', 'Okay', { duration: 0 });
      this.apiService.completeLinking();
    } catch (error) {
      if (!this.parseBrooksError(error)) {
        const message = 'Error linking the units, check the console (F12) and report the problem.';
        this.parseError(error, message);
        this.contentChanged();
      } else {
        this.contentChanged();
        this.snackBar.open('Error saving the linking, check the error list and the dots in the floorplan.', 'Error', {
          duration: 0,
        });
      }
    }
    this.saving = false;
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

  floorToHuman(floor) {
    return floorToHumanStr(floor);
  }

  /**
   * Unsubscribe from everything when destroying the component
   */
  ngOnDestroy(): void {
    if (this.activatedRoute_sub) {
      this.activatedRoute_sub.unsubscribe();
    }
    if (this.changedApartmentSubscription) {
      this.changedApartmentSubscription.unsubscribe();
    }
    if (this.nextSelectedApartmentSubscription) {
      this.nextSelectedApartmentSubscription.unsubscribe();
    }
  }
}
