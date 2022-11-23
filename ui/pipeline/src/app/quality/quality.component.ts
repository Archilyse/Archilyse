import { Component, OnDestroy, OnInit } from '@angular/core';
import { BaseComponent } from '../base.component';
import { GoogleAnalyticsService } from 'ngx-google-analytics';
import { HttpClient } from '@angular/common/http';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ApiService } from '../_services/api.service';
import { HelpDialogQualityComponent } from './help-quality/help-quality.component';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs/internal/Subscription';
import { environment } from '../../environments/environment';

const VALIDATE = 'Validate';
const NET_AREA_DEFAULT = 'HNF';

const PIPELINE_PHASES = ['labelled', 'classified', 'scaled', 'splitted', 'georeferenced', 'units_linked'];

@Component({
  selector: 'app-quality',
  templateUrl: './quality.component.html',
  styleUrls: ['./quality.component.scss'],
})
export class QualityComponent extends BaseComponent implements OnInit, OnDestroy {
  data;
  dataByPlan;
  siteErrors;
  siteWarnings;
  site_id;

  activatedRoute_sub: Subscription;

  numErrors;
  selectedArea;
  isBasicFeatureReady: Boolean;
  runningQAMessage: String;
  runningQAMessageLine2: String;
  QaAnalysisButtonDisabled: Boolean = true;
  pipelineCompleted: Boolean;

  sampleSurrButtonDisabled: Boolean = false;
  sampleSurrButtonClass: String;
  sampleSurrButtonText: String;
  sampleSurrButtonTitle: String;
  sampleSurrTaskState;

  addressPerBuilding;
  dataByBuildingAndPlan;

  basic_features_status;

  STATUS = {
    UNPROCESSED: 'UNPROCESSED',
    PENDING: 'PENDING',
    PROCESSING: 'PROCESSING',
    SUCCESS: 'SUCCESS',
    FAILURE: 'FAILURE',
  };

  constructor(
    protected $gaService: GoogleAnalyticsService,
    private http: HttpClient,
    public dialog: MatDialog,
    public snackBar: MatSnackBar,
    public apiService: ApiService,
    private router: Router,
    private activatedRoute: ActivatedRoute
  ) {
    super();
  }

  getPipelineLink(planId) {
    return `/classification/${planId}`;
  }

  async ngOnInit() {
    this.$gaService.pageView('/quality', 'Quality validation tool');
    this.resetData();

    if (!this.activatedRoute_sub) {
      const expectedParameters = ['site_id'];
      this.activatedRoute_sub = this.loadOnNewParameters(
        this.activatedRoute,
        async () => {
          try {
            this.resetData();
            this.pipelineCompleted = await this.isPipelineCompleted();
            if (this.pipelineCompleted) {
              this.isBasicFeatureReady = await this.isQAReady();
            }
            await this.getSiteData();
            await this.initSurrSampleStatus();
          } catch (e) {
            this.parseError(e);
          }
        },
        expectedParameters
      );
    }
  }

  resetData() {
    this.saveDisabled = true;
    this.saveText = VALIDATE;
    this.selectedArea = NET_AREA_DEFAULT;
    this.loading = false;
    this.error = null;
    this.basic_features_status = null;
    this.runningQAMessage = '';
    this.runningQAMessageLine2 = '';
    this.dataByPlan = null;
    this.siteErrors = null;
    this.siteWarnings = null;
  }

  async getSiteData() {
    const site = await this.apiService.getSite(this.site_id);
    this.client_site_id = site.client_site_id;
    this.sampleSurrTaskState = site.sample_surr_task_state;
  }

  onChangeArea(event) {
    this.selectedArea = event.target.value;
  }

  isPlanCorrect(data) {
    const clientIssues = Object.values(data || {});
    return clientIssues.every((issues: any[]) => !issues || !issues.length);
  }

  getDataByPlan(units) {
    const affectedClientIds = Object.keys(this.data);
    const affectedUnits = units.filter(u => affectedClientIds.includes(u.client_id));
    return affectedUnits.reduce((accum, unit: any) => {
      const planId = unit.plan_id;
      const clientId = unit.client_id;
      accum[planId] = accum[planId] || {};
      accum[planId][clientId] = accum[planId][clientId] || {};
      accum[planId][clientId] = this.data[clientId]?.slice();
      return accum;
    }, {});
  }

  async loadData() {
    try {
      this.error = null;
      this.loading = true;
      this.runningQAMessage = '';
      const site = await this.apiService.getSite(this.site_id);
      const structure = await this.apiService.getSiteBuildingAndFloors(this.site_id);

      this.addressPerBuilding = structure.buildings.reduce((accum, building) => {
        accum[building.id] = { address: `${building.street}, ${building.housenumber}` };
        return accum;
      }, {});

      if (site.qa_validation == null) {
        this.data = {};
        this.siteWarnings = [];
        this.siteErrors = [];
      } else {
        this.data = site.qa_validation;
        this.siteWarnings = this.data['site_warnings'];
        this.siteErrors = this.data['errors'];
      }

      const units = await this.apiService.getUnitsBySite(this.site_id);
      this.dataByPlan = this.getDataByPlan(units);

      this.dataByBuildingAndPlan = structure.buildings.reduce((accum, building) => {
        accum[building.id] = accum[building.id] || {};
        Object.values(building.floors).forEach((floor: any) => {
          accum[building.id][floor.plan_id] = accum[building.id][floor.plan_id] || {};
          accum[building.id][floor.plan_id] = this.dataByPlan[floor.plan_id];
        });
        return accum;
      }, {});
      this.numErrors = Object.keys(this.data).reduce((accumulator, current) => {
        const val = this.data[current];
        if (val.length) {
          return accumulator + 1;
        }
        return accumulator;
      }, 0);
      this.error = null;
      this.loading = false;
      if (this.siteErrors?.length > 0) {
        this.saveDisabled = true;
      } else {
        this.saveDisabled = false;
      }
    } catch (e) {
      this.parseError(e);
    }
  }

  async isQAReady() {
    try {
      this.runningQAMessage = 'Loading';
      this.runningQAMessageLine2 = '';
      this.QaAnalysisButtonDisabled = false;
      const site = await this.apiService.getSite(this.site_id);

      this.basic_features_status = site.basic_features_status;
      if (this.basic_features_status === this.STATUS.UNPROCESSED) {
        this.runningQAMessage = 'Click on Generate QA analysis to start.';
        return false;
      }

      if (this.basic_features_status === this.STATUS.PENDING) {
        this.runningQAMessage =
          'QA analysis is on the queue to be calculated soon, please refresh the page in a few minutes.';
        this.runningQAMessageLine2 =
          'This process can take from a few minutes up to 20-30 min, the bigger the site the longer the time. You can close this window and come back later.';
        this.QaAnalysisButtonDisabled = true;
        return false;
      }

      if (this.basic_features_status === this.STATUS.PROCESSING) {
        this.runningQAMessage = 'QA analysis is being calculated, please refresh the page in a few minutes.';
        this.QaAnalysisButtonDisabled = true;
        return false;
      }

      if (this.basic_features_status === this.STATUS.FAILURE) {
        this.runningQAMessage = 'QA analysis has failed.';

        if (site.basic_features_error?.errors) {
          this.runningQAMessageLine2 = `ERROR: ${site.basic_features_error.errors
            .map(error => {
              if (error.text) {
                return `${error.text} - ${error.human_id}`;
              }
              return error;
            })
            .join('. ')}`;
        } else {
          this.runningQAMessageLine2 = `No error provided, make sure that the pipeline is completed`;
        }
        return false;
      }

      if (this.basic_features_status === this.STATUS.SUCCESS) {
        try {
          await this.loadData();
        } catch (e) {
          this.parseError(e);
        }
        return true;
      }
    } catch (e) {
      this.parseError(e);
    }
  }

  linkToSite() {
    // URL to the admin tool
    location.replace(`${environment.adminBuildingsUrl}${this.site_id}`);
  }

  async isPipelineCompleted() {
    const pipelines = await this.apiService.getPipelinesBySite(this.site_id);
    const allTrue = pipeline => Object.values(pipeline).every(v => v === true);

    const filtered = elem =>
      Object.keys(elem)
        .filter(key => PIPELINE_PHASES.includes(key))
        .reduce((obj, key) => {
          obj[key] = elem[key];
          return obj;
        }, {});

    const pipelineCompleted = pipelines.map(filtered).every(allTrue) && !(pipelines.length === 0);
    if (!pipelineCompleted) {
      this.runningQAMessage = 'Please finish the PIPELINE for all plans before doing QA.';
    }
    return pipelineCompleted;
  }

  async onRunQaAnalysis() {
    try {
      this.resetData();
      await this.apiService.runBasicFeatures(this.site_id);
      this.saveDisabled = false;
      this.isBasicFeatureReady = await this.isQAReady();
    } catch (e) {
      this.parseError(e);
    }
  }

  async onValidate() {
    try {
      await this.apiService.updateSite(this.site_id, {
        pipeline_and_qa_complete: true,
      });
      this.saveDisabled = true;
      this.snackBar.open('QA validation saved successfully', 'Okay', {
        duration: 0,
      });
    } catch (e) {
      this.parseError(e);
    }
  }

  openHelpDialog(): void {
    this.dialog.open(HelpDialogQualityComponent, {
      id: 'helpDialog',
    });
  }

  async initSurrSampleStatus() {
    try {
      if (!this.pipelineCompleted) {
        this.sampleSurrButtonDisabled = true;
        this.sampleSurrButtonClass = 'btn-secondary';
        this.sampleSurrButtonText = 'Generate Surroundings';
        this.sampleSurrButtonTitle = 'Complete Pipeline before generating the Surroundings';
        return;
      }

      // Pipeline is completed
      if (this.sampleSurrTaskState === this.STATUS.SUCCESS) {
        this.sampleSurrButtonDisabled = false;
        this.sampleSurrButtonClass = 'btn-success';
        this.sampleSurrButtonText = 'Download Surroundings';
        this.sampleSurrButtonTitle = 'Ready to download Surroundings';
        return;
      }
      if (this.sampleSurrTaskState === this.STATUS.FAILURE) {
        this.sampleSurrButtonDisabled = false;
        this.sampleSurrButtonClass = 'btn-danger';
        this.sampleSurrButtonText = 'Re-Generate Surroundings (Failed)';
        this.sampleSurrButtonTitle = 'Generate Surroundings Failed. Try again';
        return;
      }
      if (this.sampleSurrTaskState === this.STATUS.PROCESSING || this.sampleSurrTaskState === this.STATUS.PENDING) {
        this.sampleSurrButtonDisabled = true;
        this.sampleSurrButtonClass = 'btn-warning';
        this.sampleSurrButtonText = 'Generating Surroundings';
        this.sampleSurrButtonTitle = 'Surroundings are being generated';
        return;
      }
      // UNPROCESSED or undefined
      this.sampleSurrButtonDisabled = false;
      this.sampleSurrButtonClass = 'btn-primary';
      this.sampleSurrButtonText = 'Generate Surroundings';
      this.sampleSurrButtonTitle = 'Ready to generate Surroundings';
    } catch (e) {
      this.parseError(e);
    }
  }

  autoDownloadFile(blob): void {
    const objectUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = objectUrl;
    a.download = name;
    document.body.appendChild(a);
    a.click();
  }

  async onRunSampleSurr() {
    try {
      if (this.sampleSurrTaskState === this.STATUS.SUCCESS) {
        const response = await this.apiService.downloadSampleSurroundings(this.site_id);
        const blob = new Blob([response], { type: 'text/html' });
        this.autoDownloadFile(blob);
      } else {
        await this.apiService.runSampleSurroundings(this.site_id);
        this.sampleSurrTaskState = this.STATUS.PENDING;
        await this.initSurrSampleStatus();
      }
    } catch (e) {
      this.parseError(e);
    }
  }

  ngOnDestroy(): void {
    if (this.activatedRoute_sub) {
      this.activatedRoute_sub.unsubscribe();
    }
  }
}
