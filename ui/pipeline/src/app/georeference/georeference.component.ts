import { Component, HostListener, OnDestroy, OnInit } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { HelpDialogGeoreferenceComponent } from './help-georeference/help-georeference.component';
import { ActivatedRoute, Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ApiService } from '../_services/api.service';
import { EventStreamApiService } from '../_services/eventstreamapi.service';
import { environment } from '../../environments/environment';
import { defaults as defaultControls, ScaleLine } from 'ol/control';
import { fromLonLat, toLonLat } from 'ol/proj';
import OlFeature from 'ol/Feature';
import OlMultiPolygon from 'ol/geom/MultiPolygon';
import OlStyle from 'ol/style/Style';
import OlStyleFill from 'ol/style/Fill';
import OlStyleStroke from 'ol/style/Stroke';
import { Drag } from './georeference.mouse';
import RotateFeatureInteraction from 'ol-rotate-feature';
import Select from 'ol/interaction/Select';
import { defaults as defaultInteractions } from 'ol/interaction';

const DEFAULT_MAPBOX_STYLE = 'streets-v11';

const MAPBOX_URL = (style = DEFAULT_MAPBOX_STYLE) =>
  `https://api.mapbox.com/styles/v1/mapbox/${style}/tiles/{z}/{x}/{y}?access_token=${environment.mapboxToken}`;

/**
 * We need the scale to be in meters
 */
const scaleLineControl = new ScaleLine();
scaleLineControl.setUnits('metric');

/**
 *  Margin when centering the screen, in pixels
 */
const paddingToBuildings = [200, 200, 200, 200];
const FEEDBACK_MARGIN_X = 0.1;
const FEEDBACK_MARGIN_Y = 0.1;
// https://epsg.io/3857 is a projected system covering the entire world and generally used in all map applications
const mercatorProjection = 'EPSG:3857';

import OlMap from 'ol/Map';
import OlXYZ from 'ol/source/XYZ';
import OlTileLayer from 'ol/layer/Tile';
import OlVectorLayer from 'ol/layer/Vector';
import OlView from 'ol/View';
import Vector from 'ol/source/Vector';
import { styleNormal } from '../_shared-libraries/OlMapStyles';
import { parseParams } from '../_shared-libraries/Url';
import { Subscription } from 'rxjs/internal/Subscription';
import { COOR_X, COOR_Y, polygonJsonCoordinatesStandard } from '../_shared-libraries/SimData';
import { GoogleAnalyticsService } from 'ngx-google-analytics';
import { BaseComponent } from '../base.component';
import { shouldSave } from '../_shared-libraries/Validations';
import { Subject } from 'rxjs/internal/Subject';

@Component({
  selector: 'splitting-component',
  templateUrl: './georeference.component.html',
  styleUrls: ['./georeference.component.scss'],
})
export class GeoreferenceComponent extends BaseComponent implements OnInit, OnDestroy {
  /**
   * TABLE DOCUMENTATION
   * https://www.ag-grid.com/angular-getting-started/
   */

  map: OlMap = null;
  source: OlXYZ;
  layer: OlTileLayer;

  globalLayer: OlVectorLayer;
  globalSource;

  decorationLayer: OlVectorLayer;
  decorationSource;

  decorationFloorsLayer: OlVectorLayer;
  decorationFloorsSource;

  openLayersIdToPlan;
  planIdDelta;

  view: OlView;

  footprint: OlFeature;

  rotateSelect;
  rotateInteraction;
  dragInteraction;

  toSaveAngleRadians = 0;
  toSaveAngleDegrees = 0;

  planMercatorTranslationPoint;

  // Drag controls
  dragStartX;
  dragStartY;
  dragDeltaX = 0;
  dragDeltaY = 0;

  planData;
  footprintData;
  buildingsFootprints;
  loadingPlansGeoreferenced;
  plansGeoreferenced;
  siteAndPlansData;

  currentFloorNrs;
  currentBuildingId;

  siteData;

  warnings = [];
  /** Only the plan Ids ordered in ascending order*/
  buildingsFootprintsPlanIds = [];
  buildingsFootprintsPlanIds$;

  // When they press Control map mode changes
  isRotationMode = false;
  displayClose = false;
  /**
   * Mapbox Style selected
   * light, dark, outdoors, streets, satellite
   */
  mapStyle;

  /**
   * Subscriptions
   */
  fragment_sub: Subscription;
  activatedRoute_sub: Subscription;

  constructor(
    protected $gaService: GoogleAnalyticsService,
    public dialog: MatDialog,
    public snackBar: MatSnackBar,
    public apiService: ApiService,
    public eventStreamApiService: EventStreamApiService,
    private router: Router,
    private activatedRoute: ActivatedRoute
  ) {
    super();
  }

  ngOnInit(): void {
    this.$gaService.pageView('/georeference', 'Georeference tool');
    this.error = null;
    this.loading = true;
    this.loadingPlansGeoreferenced = false;
    this.buildingsFootprintsPlanIds$ = new Subject<number[]>();

    if (!this.activatedRoute_sub) {
      const expectedParameters = ['plan_id'];
      this.activatedRoute_sub = this.loadOnNewParameters(
        this.activatedRoute,
        () => this.loadData(),
        expectedParameters
      );
    }
  }

  ngOnDestroy(): void {
    if (this.fragment_sub) {
      this.fragment_sub.unsubscribe();
    }
    if (this.activatedRoute_sub) {
      this.activatedRoute_sub.unsubscribe();
    }
  }

  changeDisplayed(e) {
    this.redrawGeoreferencedBuildings();
  }

  resetData() {
    this.saveDisabled = true;

    this.loading = true;
    this.loadingPlansGeoreferenced = false;
    this.error = null;

    this.dragStartX = null;
    this.dragStartY = null;

    this.dragDeltaX = 0;
    this.dragDeltaY = 0;

    this.toSaveAngleRadians = 0;
    this.toSaveAngleDegrees = 0;

    this.planMercatorTranslationPoint = null;

    this.isRotationMode = false;

    this.openLayersIdToPlan = {};
    this.planIdDelta = {};
  }

  async requestCHBuildingFootprints() {
    if (this.siteData.georef_proj === 'EPSG:2056') {
      await this.apiService
        .getSurroundingBuildingsFootprints(this.site_id)
        .then(response => (this.buildingsFootprints = response.data))
        .catch(error => {
          this.parseError(
            'SwissTopo building footprints are not available. You can still continue using the background OSM data'
          );
        });
    } else {
      this.buildingsFootprints = [];
    }
  }
  async validate() {
    try {
      const response = await this.apiService.getGeoreferenceValidation(this.plan_id);
      this.warnings = response.data;
    } catch (error) {
      console.log(`Error requesting geoereference validations: ${error}`);
    }
  }

  async loadData() {
    this.resetData();
    this.contentNew();

    try {
      // We get the current coordinates
      this.planData = await this.apiService.getPlanData(this.plan_id);
      this.siteData = await this.apiService.getSite(this.planData.site_id);
      this.validate();

      if (this.planData) {
        this.site_id = this.planData.site_id;
        this.siteData = await this.apiService.getSite(this.planData.site_id);
        await this.requestCHBuildingFootprints();
        this.siteAndPlansData = await this.apiService.getSiteBuildingAndFloors(this.site_id);

        const { buildingId, floorNrs } = this.getPlanFloorNrs(this.plan_id);

        this.currentFloorNrs = floorNrs;
        this.currentBuildingId = buildingId;

        this.loading = true;
        // We get the geoereferenced plans of the same site
        this.apiService.getFootprintById(this.plan_id).then(async result => {
          this.footprintData = result;
          if (this.planData.georef_x && this.planData.georef_y) {
            this.planMercatorTranslationPoint = fromLonLat(
              [this.planData.georef_x, this.planData.georef_y],
              mercatorProjection
            );
          } else {
            this.planMercatorTranslationPoint = fromLonLat([this.siteData.lon, this.siteData.lat], mercatorProjection);
          }
          this.loading = false;
          this.setUpMap();
          this.loadOtherFootprints();
        });
      } else {
        this.parseError('Error requesting plan data');
      }
    } catch (e) {
      this.parseError(e);
    }
  }

  getPlanFloorNrs(planId) {
    const planIdStr = `${planId}`;
    const floorNrs = [];
    let buildingId = null;
    if (this.siteAndPlansData?.buildings) {
      for (const building of this.siteAndPlansData.buildings) {
        for (const floorId of Object.keys(building.floors || {})) {
          const floor = building.floors[floorId];
          if (`${floor.plan_id}` === planIdStr) {
            floorNrs.push(floor.floor_number);
            buildingId = building.id;
          }
        }
      }
    }
    return {
      buildingId,
      floorNrs,
    };
  }

  @HostListener('document:keydown', ['$event'])
  handleKeyDown(e) {
    // Center the camera pressing 0
    if (e.which === 48) {
      this.centerMap();
    } else {
      if (!this.isRotationMode && this.rotateSelect) {
        this.rotateSelect.getFeatures().extend([this.footprint]);
        this.isRotationMode = true;
      }
    }
  }
  @HostListener('document:keyup', ['$event'])
  handleKeyUp() {
    if (this.isRotationMode && this.rotateSelect) {
      this.rotateSelect.getFeatures().remove(this.footprint);
      this.isRotationMode = false;
    }
  }

  setUpMap() {
    if (this.map === null) {
      this.mapStyle = DEFAULT_MAPBOX_STYLE;

      this.source = new OlXYZ({
        url: MAPBOX_URL(),
        // To avoid percy problems while testing:
        // https://stackoverflow.com/questions/22710627/tainted-canvases-may-not-be-exported
        crossOrigin: 'Anonymous',
      });

      this.globalSource = new Vector({
        features: [],
      });

      this.globalLayer = new OlVectorLayer({
        source: this.globalSource,
        style: styleNormal,
      });

      this.decorationSource = new Vector({
        features: [],
      });
      this.decorationFloorsSource = new Vector({
        features: [],
      });

      this.decorationLayer = new OlVectorLayer({
        source: this.decorationSource,
        style: styleNormal,
      });
      this.decorationFloorsLayer = new OlVectorLayer({
        source: this.decorationFloorsSource,
        style: styleNormal,
      });

      this.layer = new OlTileLayer({
        className: 'base-tile-layer',
        source: this.source,
      });

      this.view = new OlView({
        projection: mercatorProjection,
      });

      this.dragInteraction = new Drag(this.onDragStart.bind(this), this.onDragEnd.bind(this));

      const mapLib = new OlMap({
        controls: defaultControls({
          zoom: false,
        }).extend([scaleLineControl]),
        interactions: defaultInteractions().extend([this.dragInteraction]),
        layers: [this.layer, this.decorationLayer, this.decorationFloorsLayer, this.globalLayer],
        target: 'map',
        view: this.view,
      });

      // For testing purposes only, exposes the data to be tested
      window['mapLib'] = mapLib;
      window['globalSource'] = this.globalSource;
      window['decorationSource'] = this.decorationSource;
      window['decorationFloorsSource'] = this.decorationFloorsSource;

      this.map = mapLib;

      if (this.footprintData.coordinates.length >= 1) {
        this.setUpMapContent();

        this.rotateSelect = new Select();

        this.rotateInteraction = new RotateFeatureInteraction({
          style: () => {}, // We override the
          features: this.rotateSelect.getFeatures(),
        });

        // Fix to the getFeature Sentry error
        this.fixDragLibrary();

        this.rotateInteraction.on('rotatestart', () => {
          this.rotateInteraction.setAnchor(this.getCurrentPlanTranslationPoint());
          this.contentChanged();
          this.getOtherPlansDistances();
        });
        this.rotateInteraction.on('rotateend', evt => {
          this.saveDisabled = false;
          this.toSaveAngleRadians += evt.angle;
          this.toSaveAngleDegrees = (this.toSaveAngleRadians * 180) / Math.PI;
        });

        this.map.addInteraction(this.rotateInteraction);

        this.view.on('propertychange', e => {
          switch (e.key) {
            case 'resolution':
              this.correctVisibility();
              break;
          }
        });

        if (this.activatedRoute?.fragment && !this.fragment_sub) {
          this.fragment_sub = this.activatedRoute.fragment.subscribe(fragment => {
            const urlParams = parseParams(fragment);
            if (urlParams.hasOwnProperty('mapStyle')) {
              this.changeMapStyle(urlParams['mapStyle']);
            }
          });
        } else {
          console.error('Route not available');
        }
      }
    } else {
      this.clearOldContent();
      this.setUpMapContent();
    }
  }

  /**
   * ol-rotate-feature
   * Failed when while rotating we change to move method.
   * The the anchorFeature_ was null and the drag event failed.
   */
  fixDragLibrary() {
    const original = this.rotateInteraction.handleDragEvent.bind(this.rotateInteraction);
    this.rotateInteraction.handleDragEvent = function (event) {
      if (this.anchorFeature_?.getGeometry()) {
        original(event);
      }
    };
  }

  clearOldContent() {
    this.globalSource.clear();
    this.decorationSource.clear();
    this.decorationFloorsSource.clear();
  }

  setUpMapContent() {
    if (this.footprintData.coordinates.length >= 1) {
      this.addFootprint();
      this.rotateFootprint();
      this.addDecorationBuildings();
      this.getOtherPlansDistances();
      this.centerMap();
    }
  }

  onDragStart(event) {
    this.dragStartX = event.coordinate[COOR_X];
    this.dragStartY = event.coordinate[COOR_Y];
  }

  onDragEnd(event) {
    this.saveDisabled = false;
    this.dragDeltaX += event.coordinate[COOR_X] - this.dragStartX;
    this.dragDeltaY += event.coordinate[COOR_Y] - this.dragStartY;
    this.contentChanged();
    this.getOtherPlansDistances();
  }

  getCurrentPlanTranslationPoint() {
    if (!this.planMercatorTranslationPoint) {
      return [];
    }
    return [
      this.planMercatorTranslationPoint[COOR_X] + this.dragDeltaX,
      this.planMercatorTranslationPoint[COOR_Y] + this.dragDeltaY,
    ];
  }

  /**
   * For plans in the same building only
   * We calculate the delta for the bounding box.
   * As a visual feedback for the user
   */
  getOtherPlansDistances() {
    let referenceX = null;
    let referenceY = null;

    // Reference feature
    this.globalSource.forEachFeature(feature => {
      const geom = feature.getGeometry();
      const [left, top, right, bottom] = geom.getExtent();
      referenceX = left;
      referenceY = top;
    });

    // Other Floors
    this.decorationFloorsSource.forEachFeature(feature => {
      const geom = feature.getGeometry();

      const planId = this.openLayersIdToPlan[geom.ol_uid];
      const { buildingId } = this.getPlanFloorNrs(planId);

      // Only if they are in the same building we provide feedback
      if (this.currentBuildingId === buildingId) {
        const [left, top, right, bottom] = geom.getExtent();
        const width = Math.abs(right - left);
        const height = Math.abs(top - bottom);

        this.planIdDelta[planId] = {
          width,
          height,
          deltaX: Math.abs(left - referenceX),
          deltaY: Math.abs(top - referenceY),
        };
      }
    });
  }

  /**
   * Draws all the buildings provided from the backend as a surrounding
   * - building footprints
   * - already georeferenced plans from the same building
   */
  addDecorationBuildings() {
    if (Array.isArray(this.buildingsFootprints)) {
      const styleDecoBuilding = new OlStyle({
        fill: new OlStyleFill({
          color: 'rgba(255,255,255,0.25)',
        }),
        stroke: new OlStyleStroke({
          color: 'rgba(0,0,0, 0.85)',
          width: 3,
        }),
      });

      this.buildingsFootprints.forEach(bF => {
        this.addDecorationBuilding(bF, styleDecoBuilding);
      });
    }
  }

  loadOtherFootprints() {
    this.plansGeoreferenced = { data: Array() };
    this.loadingPlansGeoreferenced = true;
    this.eventStreamApiService.getGeoreferencedPlansUnderSameSite(this.plan_id).subscribe({
      next: event => {
        this.addGeoreferencedBuilding(JSON.parse(event.data));
      },
      error: error => {
        this.parseError(error.data);
      },
      complete: () => {
        this.loadingPlansGeoreferenced = false;
      },
    });
  }

  redrawGeoreferencedBuildings() {
    this.decorationFloorsSource.clear();

    if (this.plansGeoreferenced.data && Array.isArray(this.plansGeoreferenced.data)) {
      this.buildingsFootprintsPlanIds = [];
      this.plansGeoreferenced.data.forEach(plan => {
        this.addGeoreferencedBuilding(plan);
      });
      this.buildingsFootprintsPlanIds.sort();
    }
  }

  /**
   * We check all the floors with all of them
   * @param floorNrs
   * @param buildingId
   */
  isAnyFloorClose(floorNrs, buildingId) {
    // Has to be in the same building
    if (this.currentFloorNrs && floorNrs && this.currentBuildingId === buildingId) {
      for (let i = 0; i < floorNrs.length; i += 1) {
        const floorNr = floorNrs[i];
        for (let j = 0; j < this.currentFloorNrs.length; j += 1) {
          const floorNrCurrent = this.currentFloorNrs[j];
          if (Math.abs(floorNr - floorNrCurrent) <= 1) {
            return true;
          }
        }
      }
    }
    return false;
  }

  addGeoreferencedBuilding(plan) {
    const { floorNrs, buildingId } = this.getPlanFloorNrs(plan.id);

    let opacityFill = 0.04;
    let opacityStroke = 0.2;

    // Yellow
    let color = '255,232,0';
    const isDifferentBuilding = this.currentBuildingId !== buildingId;

    if (!this.displayClose || this.isAnyFloorClose(floorNrs, buildingId) || isDifferentBuilding) {
      opacityFill = 0.15;
      opacityStroke = 0.85;
    }

    if (isDifferentBuilding) {
      // Light Green
      color = '180,232,0';
    }

    const styleDecoPlan = new OlStyle({
      fill: new OlStyleFill({
        color: `rgba(${color}, ${opacityFill})`,
      }),
      stroke: new OlStyleStroke({
        color: `rgba(${color}, ${opacityStroke})`,
        width: 2,
      }),
    });

    this.buildingsFootprintsPlanIds.push(plan.id);
    this.buildingsFootprintsPlanIds$.next(this.buildingsFootprintsPlanIds);
    this.getOtherPlansDistances();
    this.addDecorationPlan(plan.id, plan.footprint, styleDecoPlan);
  }

  getMercatorProjectedFootprint(latLonFootprint) {
    const coordinates = polygonJsonCoordinatesStandard(latLonFootprint);
    const coordsOpenLayers = coordinates.map(coords => coords.map(c => c.map(d => fromLonLat(d, mercatorProjection))));

    const newFootprint = new OlFeature({
      geometry: new OlMultiPolygon(coordsOpenLayers),
    });
    return newFootprint;
  }

  /**
   * Adds a building we don't interact with, is just a visual guideline
   * @param latLonBuildingFootprint EPSG4326 coordinates of the building
   * @param style ThreeJs style to apply
   */
  addDecorationBuilding(latLonBuildingFootprint, style) {
    const newBuilding = this.getMercatorProjectedFootprint(latLonBuildingFootprint);
    newBuilding.setStyle(style);
    this.decorationSource.addFeature(newBuilding);
  }

  /**
   * Adds a plan previously georeferenced we don't interact with, is just a visual guideline
   * @param planId
   * @param latLonPlanFootprint EPSG4326 coordinates of the plan
   * @param style ThreeJs style to apply
   */
  addDecorationPlan(planId, latLonPlanFootprint, style) {
    const newFootprint = this.getMercatorProjectedFootprint(latLonPlanFootprint);
    newFootprint.setStyle(style);
    this.decorationFloorsSource.addFeature(newFootprint);
    this.openLayersIdToPlan[newFootprint.values_.geometry.ol_uid] = planId;
  }

  /**
   * Changes the mapbox map style
   * @param data
   */
  changeMap(data) {
    const newValue = `mapStyle=${data.target.value}`;
    this.router.navigate([], {
      fragment: newValue,
      relativeTo: this.activatedRoute,
      replaceUrl: true,
    });
  }

  /**
   * Adds a footprint in the given polygons to the map
   * @param polygons
   */
  addFootprint() {
    this.footprint = this.getMercatorProjectedFootprint(this.footprintData);
    // To recover the value
    this.footprint.setId('georeferencedBuilding');

    this.footprint.setStyle(
      new OlStyle({
        fill: new OlStyleFill({
          color: 'rgba(0,0,233,0.15)',
        }),
        stroke: new OlStyleStroke({
          color: 'rgba(0,73,207,0.85)',
          width: 4,
        }),
      })
    );

    this.globalSource.addFeature(this.footprint);
  }

  /**
   * We scale the footprint and rotate it according to the "plan" parameters from the backend (if set).
   * @param footprint
   */
  rotateFootprint() {
    if (this.planData.georef_rot_angle) {
      this.toSaveAngleDegrees = this.planData.georef_rot_angle;
      this.toSaveAngleRadians = (this.toSaveAngleDegrees * Math.PI) / 180;
    }
  }

  /**
   * Based in the zoom level will display the detailLayer or the globalLayer
   * @param resolution
   */
  correctVisibility() {
    this.globalLayer.setVisible(true);
  }

  /**
   * Changes de displayed map mode
   * @param mapStyle
   */
  changeMapStyle(mapStyle) {
    this.mapStyle = mapStyle;
    this.source = new OlXYZ({
      url: MAPBOX_URL(mapStyle),
    });

    this.layer.setSource(this.source);
  }

  /**
   * Centers the map in the screen.
   */
  centerMap() {
    if (this.view) {
      this.view.fit(this.globalSource.getExtent(), {
        padding: paddingToBuildings,
        constrainResolution: false,
        nearest: false,
      });

      this.correctVisibility();
    }
  }

  /**
   * Always we save angles from 0 to 360 grades
   * @param radians
   */
  radiansToAngle(radians) {
    let angles = ((radians * 180) / Math.PI) % 360;
    while (angles < 0) {
      angles += 360;
    }
    return angles;
  }

  /**
   * Save the current progress
   */
  async save() {
    this.saving = true;

    if (!(await shouldSave(this.apiService, this.plan_id))) {
      this.saving = false;
      return;
    }

    const georef_rot_angle = this.radiansToAngle(this.toSaveAngleRadians);

    const baseLonLat = toLonLat(this.getCurrentPlanTranslationPoint(), mercatorProjection);

    const georef_x = baseLonLat[COOR_X];
    const georef_y = baseLonLat[COOR_Y];

    this.apiService
      .updateGeoreference(this.plan_id, georef_rot_angle, georef_x, georef_y)
      .then(() => {
        this.saving = false;
        this.apiService.completeGeoreferencing();
        this.snackBar.open('Georeferenced saved successfully', 'Okay', {
          duration: 0,
        });
        this.validate();
        this.saveDisabled = true;
      })
      .catch(e => {
        this.saving = false;
        this.saveDisabled = false;
        this.parseError(e);
      });
  }

  /**
   * Opens the help dialog
   */
  openDialog(): void {
    this.dialog.open(HelpDialogGeoreferenceComponent, {
      id: 'helpDialog',
      minWidth: '450px',
    });
  }

  getClassDeltaX(planIdDelta) {
    return { correct: planIdDelta.deltaX < FEEDBACK_MARGIN_X, fail: planIdDelta.deltaX >= 0.1 };
  }
  getClassDeltaY(planIdDelta) {
    return { correct: planIdDelta.deltaY < FEEDBACK_MARGIN_Y, fail: planIdDelta.deltaY >= 0.1 };
  }
}
