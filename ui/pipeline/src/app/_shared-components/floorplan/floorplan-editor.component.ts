import { Box3, FontLoader, Group, Scene, WebGLRenderer } from 'three-full/builds/Three.es.js';
import { Component, EventEmitter, HostListener, Input, OnDestroy, OnInit, Output } from '@angular/core';
import {
  EditorConstants,
  isASeparator,
  isASpace,
  isAnArea,
  isFurniture,
} from '../../_shared-libraries/EditorConstants';

import { AreaService } from '../../_services/area.service';
import { EditorService } from '../../_services/editor.service';
import { FloorplanAreasLib } from './floorplan-areas-lib';
import { FloorplanCameraLib } from './floorplan-camera-lib';
import { FloorplanCommonLib } from '../../_services/floorplan/floorplan.common.lib';
import { FloorplanEditorDraw } from './floorplan-editor-draw';
import { FloorplanEditorLib } from './floorplan-editor-lib';
import { FloorplanInterfaceService } from '../../_services/floorplan/floorplan.interface.service';
import { FloorplanMouseLib } from './floorplan-mouse-lib';
import { FloorplanUnitsLib } from './floorplan-units-lib';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subscription } from 'rxjs/internal/Subscription';
import { drawError } from '../../_shared-libraries/Geometries';

/** Base Layer */
const LAYER_1 = 0.4;
/** 2nd Layer */
const LAYER_2 = 0.8;
/** 3rd Layer */
const LAYER_3 = 1.2;
/** 4th Layer */
const LAYER_4 = 1.6;

/**
 * Container for the editor and the sidebar
 * Provides data for both elements
 */
@Component({
  selector: 'floorplan-editor',
  templateUrl: './floorplan-editor.component.html',
  styleUrls: ['./floorplan-editor.component.scss'],
})
export class FloorplanEditorComponent implements OnInit, OnDestroy {
  modelStructure;

  @Output() reloadModel = new EventEmitter();
  @Output() changedCamera = new EventEmitter();

  @Input() cameraToKeep;
  @Input() selectedByDefault;

  @Input() colorIndexes;

  // Controls if we render the furniture
  @Input() addFurniture;

  @Input() logic: FloorplanInterfaceService;
  @Input() SCALE = 1;

  @Input() uniqueId = '';

  @Input() areaTypes;

  // Display a background image
  @Input() backgroundImg;
  @Input() backgroundImgWidth;
  @Input() backgroundImgHeight;
  @Input() backgroundImgRotation;
  @Input() backgroundImgShiftX;
  @Input() backgroundImgShiftY;
  @Input() backgroundImgScale;

  backgroundImgElement;

  @Input()
  get model() {
    return this.modelStructure;
  }

  set model(val) {
    this.modelStructure = val;
  }

  container;

  top; /** Here we store the top & left of the container */
  left;
  width; /** Here we store the width & height of the container */
  height;

  /** Camera controls */
  camera;
  controls;
  renderer;
  scene;

  initialZoom;

  controlsListener;

  cameraInfo;

  /** Calculations mouse to 3d: */
  raycaster;
  mouse;

  objectsToIntersect;

  /** Highlight Click */
  previousMeshMaterial = null;
  previousMesh = null;

  /** HighlightOver */
  previousMeshOverMaterial = null;
  previousMeshOver = null;
  selectedMeshes = [];
  previousMaterials = [];

  buildingStructure;

  /** On window Resize, (We need to store it to unsubscribe later) */
  windowListener;
  mousemoveListener;
  mouseoutListener;
  mousedownListener;
  mouseupListener;

  /** Fonts and texts */
  _font3d;
  textGroups = {};

  error;

  isoAngle = 0;
  isoDistance = 100000;

  renderTimeout;
  intersectTimeout;

  removeAreasSubscription: Subscription;
  getAreasSubscription: Subscription;
  oldClassSubscription: Subscription;
  cameraSubscription: Subscription;
  viewFloorplanSubscription: Subscription;
  nextSelectedApartmentSubscription: Subscription;
  changeAngleSubscription: Subscription;
  errorSubscription: Subscription;

  constructor(public areaService: AreaService, public editorService: EditorService, public snackBar: MatSnackBar) {}

  ngOnInit() {
    this.load(() => {});
  }

  async load(onComplete) {
    this.error = null;

    // We need to load a typeface to use it in the 3d environment
    this.loadFonts(() => {
      try {
        this.init3d();
        this.subscribeToCenterTheCameraEvent();
        this.subscribeToFloorplanVisibilityEvent();
        onComplete();
      } catch (e) {
        this.error = 'Error initializing the 3d environment';
        console.error('Initializing error', e);
      }
    });
  }

  /**
   * We load the helvetiker_regular typeface to have it ready for the scene
   * @param onComplete
   */
  loadFonts(onComplete) {
    try {
      const loader = new FontLoader();
      loader.load('assets/typeface/helvetiker_regular.typeface.json', response => {
        this._font3d = response;
        onComplete();
      });
    } catch (e) {
      this.error = `Fonts couldn't be loaded, please refresh the page`;
      console.error('Fonts loading error', e);
    }
  }

  init3d() {
    // camera

    this.container = document.getElementById(`floorplanGraph${this.uniqueId}`);

    if (this.container) {
      FloorplanMouseLib.setUpMouseEvents(this);

      this.windowListener = this.onWindowResize.bind(this);
      window.addEventListener('resize', this.windowListener, false);

      // webGL renderer
      this.renderer = new WebGLRenderer({
        alpha: true,
        antialias: true,
        preserveDrawingBuffer: true, // required to support .toDataURL()
      });

      // scene
      this.scene = new Scene();

      FloorplanCameraLib.setUpCamera(this);

      this.renderer.setSize(this.width, this.height); //
      this.container.appendChild(this.renderer.domElement);

      /**
       * Original data for simple display
       */

      this.buildingStructure = new Group();
      this.addFloorplanByStructure(this.buildingStructure);

      FloorplanCameraLib.centerCamera(this);

      this.calculateObjectsToIntersect();

      FloorplanEditorLib.loadBackgroundImg(this);
      this.subscribeToServices();

      this.render();
    } else {
      console.error('DOM Id `floorplanGraph` not found');
    }
  }

  @HostListener('document:keydown.space', ['$event'])
  hideAll(e) {
    this.logic.handleKeyUp(this, e, 'space');
    if (this.backgroundImg) {
      e.preventDefault();
      this.buildingStructure.visible = false;
      this.render();
    }
  }

  @HostListener('document:keyup.space', ['$event'])
  showAll(e) {
    this.logic.handleKeyUp(this, e, 'space');
    if (this.backgroundImg) {
      e.preventDefault();
      this.buildingStructure.visible = true;
      this.render();
    }
  }

  /** We display only the not defined */
  @HostListener('document:keydown.m', ['$event'])
  hideDefined(e) {
    e.preventDefault();
    this.logic.handleKeyDown(this, e, 'm');
    this.render();
  }

  @HostListener('document:keyup.m', ['$event'])
  showDefined(e) {
    e.preventDefault();
    this.logic.handleKeyUp(this, e, 'm');
    this.objectsToIntersect.forEach(oTI => {
      oTI.visible = true;
      if (isAnArea(oTI.parent.userData.type)) {
        oTI.material.transparent = true;
        oTI.material.emissive.r = oTI.material.color.r;
        oTI.material.emissive.g = oTI.material.color.g;
        oTI.material.emissive.b = oTI.material.color.b;
        oTI.scale.set(1, 1, 1);
      }
    });
    this.render();
  }

  /**
   * Other components can use the editor service to center the camera in the scene
   */
  subscribeToCenterTheCameraEvent() {
    if (!this.cameraSubscription) {
      this.cameraSubscription = this.editorService.nextCenterCamera.subscribe(center => {
        if (center) {
          FloorplanCameraLib.centerCamera(this);
          this.render();
        }
      });
    }
  }

  subscribeToFloorplanVisibilityEvent() {
    if (!this.viewFloorplanSubscription) {
      this.viewFloorplanSubscription = this.editorService.viewFloorplan.subscribe(visible => {
        if (this.backgroundImgElement) {
          this.backgroundImgElement.visible = visible;
          this.render();
        }
      });
    }
  }

  subscribeToServices() {
    // We always subscribe to errors highlight
    FloorplanCommonLib.subscribeToError(this);
    this.logic.subscribeToServices(this);
  }

  /**
   * Update the scene with a delay to avoid render twice very quickly
   */
  render() {
    const delayedTimeoutSecs = 300;
    clearTimeout(this.renderTimeout);
    this.renderTimeout = setTimeout(() => {
      this.forceRender();
    }, delayedTimeoutSecs);
  }

  forceRender() {
    this.renderer.render(this.scene, this.camera);
  }

  /**
   * We prepare the elements the mouse can intersect with
   * Only elements that are visible.
   * 2 different sets: Normal and OnDrop (When dragging and dropping new elements)
   */
  calculateObjectsToIntersect() {
    this.objectsToIntersect = FloorplanEditorLib.concatIfVisibleGroupOfGroups([], this.buildingStructure, false);
  }

  calculateObjectsToIntersectDelayed() {
    const delayedTimeoutSecs = 600;
    clearTimeout(this.intersectTimeout);
    this.intersectTimeout = setTimeout(() => {
      this.calculateObjectsToIntersect();
    }, delayedTimeoutSecs);
  }

  /**
   * Me analyze and center in the scene a model structure
   * @param parentStructure
   */
  addFloorplanByStructure(parentStructure) {
    if (this.modelStructure) {
      this.analyzeStructure(parentStructure, this.modelStructure, 0, EditorConstants.DEFAULT_FLOOR);

      this.scene.add(parentStructure);

      const buildingBounds = new Box3().setFromObject(this.scene);

      const deltaX = (buildingBounds.max.x + buildingBounds.min.x) / 2;
      const deltaY = (buildingBounds.max.y + buildingBounds.min.y) / 2;

      // Center the scene
      this.scene.translateY(-deltaY);
      this.scene.translateX(-deltaX);

      this.render();
    } else {
      console.error('modelStructure not found', this.modelStructure);
    }
  }

  /**
   * We go through the model structure in a recursive way
   * We display the elements we find on it
   * @param parentStructure
   * @param structure
   * @param i
   * @param floorNr
   * @param insideArea
   */
  analyzeStructure(parentStructure, structure, i, floorNr, insideArea = false) {
    let currentObject;
    if (structure.type) {
      if (structure.type === EditorConstants.OPENING_NOT_DEFINED) {
        currentObject = FloorplanEditorDraw.drawGenericElement(false, this.areaService, parentStructure, structure);

        /**
         * This features can be disabled to generate previews imgs
         */
      } else if (isFurniture(structure.type)) {
        if (structure.type === EditorConstants.STAIRS || this.addFurniture) {
          currentObject = FloorplanEditorDraw.drawGenericElement(false, this.areaService, parentStructure, structure);
        } else {
          // We don't display furniture
          currentObject = parentStructure;
        }
        /** Separators */
      } else if (isASeparator(structure.type)) {
        // ************ structure.footprint.coordinates

        currentObject = FloorplanEditorDraw.drawWalls(
          false,
          this.areaService,
          this.logic,
          parentStructure,
          structure,
          structure.type,
          structure.position.coordinates,
          structure.footprint
        );

        /** AreaType */
      } else if (isAnArea(structure.type) || isASpace(structure.type)) {
        let color = [0xddcccc, 0xccbbbb, 0xbbaaaa]; // B/N
        if (insideArea) {
          color = [FloorplanAreasLib.getColor(this.colorIndexes, insideArea)];
        }

        const resultColor = this.logic.analyzeStructureColorAreas(this, structure);

        if (resultColor) {
          color = resultColor;
        }

        let finalStructure = structure;
        if (floorNr !== EditorConstants.DEFAULT_FLOOR) {
          finalStructure = Object.assign({}, structure);
        }
        finalStructure.floorNr = floorNr;

        currentObject = FloorplanEditorDraw.drawAreas(
          !insideArea,
          this.areaService,
          this.logic,
          this.SCALE,
          parentStructure,
          finalStructure,
          color,
          this._font3d,
          structure.position.coordinates,
          structure.footprint,
          i
        );

        /** OpeningType */
      } else if (structure.type === EditorConstants.DOOR || structure.type === EditorConstants.ENTRANCE_DOOR) {
        const polygonCoordinatesAndPosition = [];

        const objectGroup = new Group();

        if (structure.footprint) {
          // ************ structure.footprint.coordinates
          polygonCoordinatesAndPosition.push({
            coor: structure.footprint,
          });
          currentObject = FloorplanEditorDraw.drawDoors(objectGroup, structure.footprint);
        }

        polygonCoordinatesAndPosition.forEach(data => {
          currentObject = FloorplanEditorDraw.drawPolygonsAndRegister(
            false,
            objectGroup,
            this.areaService,
            null,
            1,
            structure,
            structure.type,
            data.coor,
            structure.type === EditorConstants.DOOR ? 0x999999 : 0x666666,
            null,
            LAYER_4,
            null,
            0.6
          );
        });

        /**
         * Opening must be the last polygon
         */
        if (structure.opening_points) {
          // ************ structure.opening_points.coordinates
          structure.opening_points.forEach(opening => {
            const points = FloorplanEditorDraw.drawOpenings(objectGroup, opening);
            polygonCoordinatesAndPosition.push({
              coor: [points],
            });
          });
        }

        objectGroup.userData = structure;
        parentStructure.add(objectGroup);

        FloorplanEditorDraw.centerObject(objectGroup, structure.position.coordinates);
      } else if (
        structure.type === EditorConstants.WINDOW_ENVELOPE ||
        structure.type === EditorConstants.WINDOW_INTERIOR ||
        structure.type === EditorConstants.WINDOW
      ) {
        // ************ structure.footprint.coordinates,

        currentObject = FloorplanEditorDraw.drawWindows(
          false,
          this.areaService,
          parentStructure,
          structure.type,
          structure
        ); // Over the walls.

        /** Full unit */
      } else if (structure.type === 'UnitType.NOT_DEFINED') {
        currentObject = parentStructure;
      } else if (structure.type === 'LayoutType.APARTMENT' || structure.type === 'LayoutType.NOT_DEFINED') {
        currentObject = parentStructure;
        /** Floor */
      } else if (structure.type === 'floor') {
        currentObject = parentStructure;

        /** Undefined */
      } else if (structure.type === 'to be filled') {
      } else {
        console.error('UNKNOWN analyzeStructure ', structure.type);
      }
    }

    if (structure.children) {
      structure.children.forEach(child => {
        this.analyzeStructure(currentObject, child, i + 1, floorNr, insideArea);
      });
    }

    if (structure.errors) {
      structure.errors.forEach((error, index) => {
        drawError(parentStructure, this.logic, error, this._font3d, index);
      });
    }
  }

  /**
   * When window is resized we recalculate container properties,
   * canvas size, camera and we render again
   */
  onWindowResize() {
    const props = FloorplanEditorLib.containerProps(this);

    if (this.renderer && this.camera) {
      this.renderer.setSize(this.width, this.height);
      this.camera = Object.assign(this.camera, props);
      this.camera.updateProjectionMatrix();
      this.renderer.render(this.scene, this.camera);
    }
  }

  clickUnit(objectData) {
    FloorplanUnitsLib.clickUnit(this, objectData);
    this.render();
  }

  /** Unsubscribe before destroying */
  ngOnDestroy(): void {
    if (this.controls) {
      this.controls.removeEventListener('change', this.controlsListener);

      FloorplanCameraLib.disableCameraControls(this.controls);
    }

    if (this.container) {
      /** Remove current events */
      this.container.removeEventListener('mousemove', this.mousemoveListener);
      this.container.removeEventListener('mouseout', this.mouseoutListener);
      this.container.removeEventListener('mousedown', this.mousedownListener);
      this.container.removeEventListener('mouseup', this.mouseupListener);
    }

    if (this.removeAreasSubscription) {
      this.removeAreasSubscription.unsubscribe();
    }
    if (this.getAreasSubscription) {
      this.getAreasSubscription.unsubscribe();
    }
    if (this.oldClassSubscription) {
      this.oldClassSubscription.unsubscribe();
    }
    if (this.cameraSubscription) {
      this.cameraSubscription.unsubscribe();
    }
    if (this.viewFloorplanSubscription) {
      this.viewFloorplanSubscription.unsubscribe();
    }
    if (this.nextSelectedApartmentSubscription) {
      this.nextSelectedApartmentSubscription.unsubscribe();
    }
    if (this.changeAngleSubscription) {
      this.changeAngleSubscription.unsubscribe();
    }
    if (this.errorSubscription) {
      this.errorSubscription.unsubscribe();
    }
  }
}
