import { async, ComponentFixture } from '@angular/core/testing';
import { FloorplanEditorComponent } from './floorplan-editor.component';
import { afterEachFloorplan, beforeEachComponent, beforeEachSetUp } from './floorplan-test-lib';
import { FloorplanCameraLib } from './floorplan-camera-lib';

describe('Floorplan camera library', () => {
  let comp: FloorplanEditorComponent;
  let fixture: ComponentFixture<FloorplanEditorComponent>;

  beforeEach(async(beforeEachSetUp));

  beforeEach(async end => {
    const res = beforeEachComponent();
    comp = res.comp;
    fixture = res.fixture;
    await comp.load(end);
  });

  afterEach(() => {
    afterEachFloorplan(fixture);
  });

  it('should create the camera control in normal view and disable them', () => {
    FloorplanCameraLib.setUpCamera(comp);
    FloorplanCameraLib.setUpControls(comp);

    FloorplanCameraLib.enableCameraControls(comp.controls);

    expect(comp.controls.enableZoom).toBe(true);
    expect(comp.controls.enablePan).toBe(true);
    expect(comp.controls.enableRotate).toBe(false);

    FloorplanCameraLib.centerCamera(comp);

    FloorplanCameraLib.disableCameraControls(comp.controls);

    expect(comp).toBeDefined();
    expect(comp.controls).toBeDefined();
    expect(comp.controls.enableZoom).toBe(false);
    expect(comp.controls.enablePan).toBe(false);
    expect(comp.controls.enableRotate).toBe(false);
    expect(comp.controls.mouseButtons).toEqual({});
  });
});
