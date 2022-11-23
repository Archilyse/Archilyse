import { async, ComponentFixture } from '@angular/core/testing';
import { FloorplanEditorComponent } from './floorplan-editor.component';
import { afterEachFloorplan, beforeEachComponent, beforeEachSetUp } from './floorplan-test-lib';
import { FloorplanMouseLib } from './floorplan-mouse-lib';

describe('Floorplan mouse library', () => {
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

  it('should set up the mouse events', () => {
    expect(comp).toBeDefined();

    FloorplanMouseLib.setUpMouseEvents(comp);

    expect(comp.mousemoveListener).toBeDefined();
    expect(comp.mouseoutListener).toBeDefined();
    expect(comp.mousedownListener).toBeDefined();
    expect(comp.mouseupListener).toBeDefined();
  });

  it('should set up the mouse events', () => {
    const eventMove = { clientX: 50, clientY: 50, preventDefault: () => {} };
    const eventClick = { clientX: 100, clientY: 100, button: 0, preventDefault: () => {} };

    FloorplanMouseLib.onMouseUpdate(comp, eventMove);

    expect(comp.mouse.x).toBeLessThan(2);
    expect(comp.mouse.x).toBeGreaterThan(-2);

    expect(comp.mouse.y).toBeLessThan(2);
    expect(comp.mouse.y).toBeGreaterThan(-2);

    FloorplanMouseLib.onMouseMove(comp, eventMove);

    expect(comp.mouse.x).toBeLessThan(2);
    expect(comp.mouse.x).toBeGreaterThan(-2);

    expect(comp.mouse.y).toBeLessThan(2);
    expect(comp.mouse.y).toBeGreaterThan(-2);

    FloorplanMouseLib.onMouseClick(comp, eventClick);
    FloorplanMouseLib.onMouseUp(comp, eventClick);

    expect(comp.error).toBeNull();
  });
});
