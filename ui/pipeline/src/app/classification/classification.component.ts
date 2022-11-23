import { BaseComponent, SAVED } from '../base.component';
import { Component, HostListener, OnDestroy, OnInit } from '@angular/core';

import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../_services/api.service';
import { AreaService } from '../_services/area.service';
import { BrooksHelper } from '../_shared-libraries/BrooksHelper';
import { EditorAnalysis } from '../_shared-libraries/EditorAnalysis';
import { EditorService } from '../_services/editor.service';
import { FloorplanClassificationService } from '../_services/floorplan/floorplan.classification.service';
import { GoogleAnalyticsService } from 'ngx-google-analytics';
import { HelpDialogClassificationComponent } from './help-classification/help-classification.component';
import { ImgService } from '../_services/img.service';
import { LocalStorage } from '../_shared-libraries/LocalStorage';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subscription } from 'rxjs/internal/Subscription';
import { shouldSave } from '../_shared-libraries/Validations';

@Component({
  selector: 'classification-component',
  templateUrl: './classification.component.html',
  styleUrls: ['./classification.component.scss'],
})
export class ClassificationComponent extends BaseComponent implements OnInit, OnDestroy {
  // Less than this number the help index for the user would be displayed
  // The index number help the user to know the shortcut to classify faster
  NUM_ITEMS_TO_DISPLAY_INDEX_NR = 20;

  isAdmin;

  modelStructure;
  areaTypes;
  areaTypeStructure;
  areaTypesDefined;
  areaTypesFiltered;
  areaFilters;

  brooksViolation = false;
  blockingViolations = false;

  areaLevels;
  selectedAreaLevel = '';

  selectedByDefault = null;

  /** Camera for the current layout */
  camera;

  selectedFeature;

  /** The color list defined to display in each area in the same order*/
  areaColors;

  statistics;
  numNotDefined;

  // Display a background image in the floorplan editor
  backgroundImg;
  backgroundImgWidth;
  backgroundImgHeight;
  backgroundImgScale;
  backgroundImgRotation;
  backgroundImgShiftX;
  backgroundImgShiftY;

  changedAreaSubscription: Subscription;
  activatedRoute_sub: Subscription;

  loadingAutoClassify = false;
  isAutoClassified = false;

  selectedFilter;

  constructor(
    protected $gaService: GoogleAnalyticsService,
    public apiService: ApiService,
    public imgService: ImgService,
    public areaService: AreaService,
    public editorService: EditorService,
    public dialog: MatDialog,
    public snackBar: MatSnackBar,
    private activatedRoute: ActivatedRoute,
    public logic: FloorplanClassificationService
  ) {
    super();
  }

  ngOnInit(): void {
    this.$gaService.pageView('/classification', 'Classification tool');
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

  areAllAreasUndefined() {
    const areaTypesDict = this.areaService.getAreaTypesDict(this.plan_id);
    return Object.values(areaTypesDict).every(a => a === 'NOT_DEFINED');
  }

  async displayCurrentValidationErrors() {
    try {
      const areaTypesDict = this.areaService.getAreaTypesDict(this.plan_id);
      const violations = await this.apiService.validateAreaTypes(this.plan_id, areaTypesDict);
      if (!this.areAllAreasUndefined()) {
        this.displayViolations(violations);
      }
    } catch (error) {
      const isValidationError = error?.status === 400;
      if (isValidationError) {
        console.log(`Controlled error validating area types ${JSON.stringify(error)}`);
      } else {
        this.parseError(error);
      }
    }
  }

  async loadData() {
    this.contentNew();
    this.loading = true;
    this.blockingViolations = false;

    try {
      await this.requestPlanData(this.apiService, this.plan_id);
      await this.getModelStructure(this.plan_id, false);
    } catch (e) {
      this.parseError(e);
    }
    this.displayCurrentValidationErrors();
  }

  async getModelStructure(plan_id: string, auto_classified: boolean) {
    /**
     * First we request the classified
     */
    if (auto_classified) {
      this.loadingAutoClassify = true;
    }
    const siteData = await this.apiService.getSite(this.planData.site_id);
    this.areaTypeStructure = await this.apiService.getClassificationScheme(siteData.classification_scheme);
    this.areaFilters = await this.apiService.getAreaFilters(siteData.classification_scheme);

    let dataManuallyClassified;
    try {
      dataManuallyClassified = await this.apiService.getBrooksById(plan_id, true);
      // We ignore the error, it's normal that fails and the second request works
    } catch (e) {}

    /**
     * If it doesn't exist, we request the NOT manually_classified
     */

    let modelStr;
    if (dataManuallyClassified) {
      modelStr = dataManuallyClassified;
    } else {
      modelStr = await this.apiService.getBrooksById(plan_id, false).catch(e => {
        this.parseError(e);
      });
    }

    if (!this.error) {
      if (modelStr?.['msg']) {
        this.error = modelStr['msg'];
      } else {
        await this.imgService.loadBackgroundImg(this, this.planData, this.apiService);
        await this.areaService.setReferenceBrooksModel(plan_id, modelStr, auto_classified);
        this.error = null;
        this.loading = false;

        this.modelStructure = modelStr;
        this.fixAreaTypes(siteData.classification_scheme);
        this.reloadModel();

        if (!this.changedAreaSubscription) {
          this.changedAreaSubscription = this.editorService.changedArea.subscribe(nextChange => {
            if (nextChange) {
              this.updateStatistics();
              this.contentChanged();
            }
          });
        }
      }

      if (auto_classified) {
        this.loadingAutoClassify = false;
        this.isAutoClassified = true;
        this.contentChanged();
      }
    }

    if (this.selectedFilter in this.areaFilters) {
      this.areaTypesFiltered = this.areaTypesDefined.filter(at => this.areaFilters[this.selectedFilter].includes(at));
    }
  }

  /**
   * Me make sure that the important elements are at the beginning of the list
   */
  fixAreaTypes(classification_scheme) {
    const classification_scheme_to_min_level = {
      ARCHILYSE: 0,
      ARCHILYSE2: 0,
      MIGROS_COMPETITION: 0,
      UNIFIED: 0,
      POST: 2,
    };

    const classification_scheme_to_default_filter = {
      UNIFIED: 'RESIDENTIAL',
      ARCHILYSE: 'RESIDENTIAL',
      ARCHILYSE2: 'RESIDENTIAL',
      MIGROS_COMPETITION: 'RESIDENTIAL',
      POST: 'No filter',
    };

    const areaData = BrooksHelper.getAreaData(this.areaTypeStructure);
    this.areaTypes = BrooksHelper.getAreaTypes(areaData);
    this.areaColors = BrooksHelper.getAreaColors(areaData);

    // We need to communicate to the area service the area color because is needed to display brooks for clasification
    this.areaService.setColors(this.areaColors);
    this.areaLevels = BrooksHelper.getAreaLevels(
      this.areaTypeStructure,
      classification_scheme_to_min_level[classification_scheme]
    );
    this.selectedFilter = classification_scheme_to_default_filter[classification_scheme];
    this.areaTypesDefined = this.areaTypes.filter(at => at !== 'NOT_DEFINED');
    this.filterAreaTypes();
  }

  /**
   * User changes the value of the select filter
   * @param event
   */
  changeFilterAreaTypes(event) {
    const val = event.target.value;
    if (val) {
      this.selectedAreaLevel = val;
    } else {
      this.selectedAreaLevel = '';
    }
    this.filterAreaTypes();
  }

  getAreaFilterNames() {
    return Object.keys(this.areaFilters);
  }

  setAreaFilter(event) {
    const val = this.selectedFilter;
    if (val === 'No filter') {
      this.areaTypesFiltered = this.areaTypesDefined;
    } else {
      this.areaTypesFiltered = this.areaTypesDefined.filter(at => this.areaFilters[val].includes(at));
    }
  }

  /**
   * From all the area Types, we select only those who belong to a selected area level
   * For each one, we find it's parents and then try to match
   */
  filterAreaTypes() {
    if (this.selectedAreaLevel !== '') {
      this.areaTypesFiltered = this.areaTypesDefined.filter(aT =>
        BrooksHelper.getAreaLevelStructure(BrooksHelper.humanToType(aT), this.areaTypeStructure).includes(
          this.selectedAreaLevel
        )
      );
    } else {
      this.areaTypesFiltered = this.areaTypesDefined;
    }
  }

  levelHasAreaTypes(areaLevel) {
    return (
      this.areaTypesFiltered.filter(areaType => this.getAreaTypeLevels(areaType).includes(areaLevel.val)).length > 0
    );
  }

  hasNoAreaLevel(areaType) {
    return this.getAreaTypeLevels(areaType).length === 0;
  }

  getAreaTypeLevels(areaType) {
    return BrooksHelper.getAreaLevelStructure(BrooksHelper.humanToType(areaType), this.areaTypeStructure);
  }

  /**
   * Calculation of the number of areas of each type
   */
  updateStatistics() {
    this.statistics = EditorAnalysis.analyzeModelStructure(this.modelStructure, this.areaService, this.areaTypes);

    if (this.statistics?.['NOT_DEFINED']) {
      this.numNotDefined = this.statistics['NOT_DEFINED'].length;
    }
  }

  @HostListener('document:keydown', ['$event'])
  handleKeyDown(e) {
    // Center the camera pressing 0
    if (e.which === 48) {
      e.preventDefault();
      this.editorService.centerCamera(true);

      // Numbers 1 to 9
    } else if (e.which > 48 && e.which <= 57) {
      e.preventDefault();

      if (this.areaTypesDefined) {
        const index = (e.shiftKey ? 10 : 0) + e.which - 48;
        this.selectFeature(this.areaTypesDefined[index - 1]);
      }

      // Shift key
    } else if (e.shiftKey) {
      e.preventDefault();

      if (this.areaTypesDefined) {
        this.selectFeature(this.areaTypesDefined[9]);
      }
    }
  }

  setBrooksErrorsEmpty() {
    const previous = this.modelStructure;
    previous.errors = [];
    this.resetBrooks(previous);
  }

  resetBrooks(newBrooks) {
    // This forces the model structure to reload
    this.modelStructure = null;
    setTimeout(() => {
      this.modelStructure = newBrooks;
    }, 10);
  }

  changedCamera(currentCamera) {
    this.camera = currentCamera;
  }

  reloadModel() {
    const ms = this.modelStructure;
    this.modelStructure = null;

    setTimeout(async () => {
      this.modelStructure = ms;
      this.updateStatistics();
    }, 0);
  }

  selectFeature(i) {
    this.selectedFeature = i;
    this.editorService.setSelectedArea(i);
  }

  displayViolations(violations) {
    this.brooksViolation = this.parseBrooksError(violations);
    this.blockingViolations = violations.errors.some(v => v.is_blocking === 1);
    this.updatePipelineStatus();
  }

  async saveValidateAreasAndDisplayError() {
    const areaTypesDict = this.areaService.getAreaTypesDict(this.plan_id);
    this.setBrooksErrorsEmpty();
    const violations = await this.apiService.updateAreaTypes(this.plan_id, areaTypesDict);
    this.displayViolations(violations);
  }

  updatePipelineStatus() {
    if (this.blockingViolations || this.areAllAreasUndefined()) {
      this.apiService.invalidateClassification();
    } else {
      this.apiService.completeClassification();
    }
  }

  async save() {
    this.saving = true;

    if (!(await shouldSave(this.apiService, this.plan_id))) {
      this.saving = false;
      return;
    }

    this.saveValidateAreasAndDisplayError();
    if (!this.brooksViolation) {
      this.snackBar.open('Classification saved successfully', 'Okay', {
        duration: 0,
      });
    } else {
      this.snackBar.open(
        'Error classifying the areas, please check the error list and the dots in the floorplan.',
        'Error',
        {
          duration: 0,
        }
      );
    }
    this.saveText = SAVED;
    this.saveDisabled = true;
    this.saving = false;
  }

  parseBrooksError(violations) {
    if (violations.errors?.length > 0) {
      this.saving = false;
      const previous = this.modelStructure;
      previous.errors = violations.errors;
      this.resetBrooks(previous);
      return true;
    }
    return false;
  }

  openDialog(): void {
    this.dialog.open(HelpDialogClassificationComponent, {
      id: 'helpDialog',
      minWidth: '450px',
    });
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

  /**
   * Unsubscribe from everything when destroying the component
   */
  ngOnDestroy(): void {
    if (this.changedAreaSubscription) {
      this.changedAreaSubscription.unsubscribe();
    }
    if (this.activatedRoute_sub) {
      this.activatedRoute_sub.unsubscribe();
    }
  }
}
