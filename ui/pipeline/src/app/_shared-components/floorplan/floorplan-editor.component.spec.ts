import { async, ComponentFixture } from '@angular/core/testing';

import { FloorplanEditorComponent } from './floorplan-editor.component';
import { By } from '@angular/platform-browser';
import { afterEachFloorplan, beforeEachComponent, beforeEachSetUp } from './floorplan-test-lib';

describe('Floorplan editor component', () => {
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

  it('should create component', () => {
    expect(comp).toBeDefined();
  });

  it('should have loaded the model structures', () => {
    expect(comp.modelStructure).toBeDefined();
    expect(comp.modelStructure.type).toBe('LayoutType.NOT_DEFINED');
  });

  it('should have loaded the area Types', () => {
    expect(comp.areaTypes.length).toBeGreaterThan(15);
  });

  it('should have loaded the camera', () => {
    expect(comp.camera).toBeDefined();
    expect(comp.camera.uuid).toBeDefined();
    expect(comp.cameraInfo).toBeDefined();
    expect(comp.cameraInfo.rotationX).toBeDefined();
    expect(comp.cameraSubscription).toBeDefined();
  });

  it('should have set up the mouse events', () => {
    expect(comp.mouse).toBeDefined();
    expect(comp.mouse.x).toBeDefined();
    expect(comp.mouse.y).toBeDefined();

    expect(comp.mousedownListener).toBeDefined();
    expect(comp.mousemoveListener).toBeDefined();
    expect(comp.mouseoutListener).toBeDefined();
    expect(comp.mouseupListener).toBeDefined();
  });

  it('should have the raycaster function defined', () => {
    expect(comp.raycaster).toBeDefined();
  });

  it('should have a windowListener function defined', () => {
    expect(comp.windowListener).toBeDefined();
  });

  it('should have nothing selected by default', () => {
    expect(comp.selectedMeshes).toBeDefined();
    expect(comp.selectedMeshes.length).toBe(0);
  });

  it('should have registered objects to intersect', () => {
    expect(comp.objectsToIntersect).toBeDefined();
    expect(comp.objectsToIntersect.length).toBe(1);

    expect(comp.mouse).toBeDefined();
  });

  it('should have the component coordenates registered', () => {
    // Here we store the top & left of the container
    expect(comp.top).toBeGreaterThanOrEqual(0);
    expect(comp.left).toBeGreaterThanOrEqual(0);

    // Here we store the width & height of the container
    expect(comp.width).toBeGreaterThan(100, 'Width should be for sure more than 100 px');
    expect(comp.height).toBeGreaterThan(100, 'Height should be for sure more than 100 px');
  });

  it('should have a canvas created', () => {
    const canvas = fixture.debugElement.query(By.css('canvas'));
    expect(canvas).toBeDefined();
  });
});
