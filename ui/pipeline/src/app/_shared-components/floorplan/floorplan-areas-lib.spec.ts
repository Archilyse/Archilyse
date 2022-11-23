import { async, ComponentFixture } from '@angular/core/testing';
import { FloorplanEditorComponent } from './floorplan-editor.component';
import { afterEachFloorplan, beforeEachComponent, beforeEachSetUp } from './floorplan-test-lib';
import { FloorplanAreasLib } from './floorplan-areas-lib';

describe('Floorplan areas library', () => {
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

  it('should get the proper color for the area', () => {
    const COLORS_HEX = [0xff1a54, 0x3cb44b, 0xffe119];
    const COLORS = ['#ff1a54', '#3cb44b', '#ffe119', '#4769e5'];

    expect(FloorplanAreasLib.getColor(COLORS_HEX, 1)).toBe(0x3cb44b);
    expect(FloorplanAreasLib.getColor(COLORS_HEX, 2)).toBe(0xffe119);

    expect(FloorplanAreasLib.getColor(COLORS_HEX, 999)).toBe('#898989');

    expect(FloorplanAreasLib.getColor(COLORS, 1)).toBe('#3cb44b');
    expect(FloorplanAreasLib.getColor(COLORS, 2)).toBe('#ffe119');

    expect(FloorplanAreasLib.getColor(COLORS, 999)).toBe('#898989');
  });

  it('should create component', () => {
    expect(comp).toBeDefined();

    /** TODO: To be tested:
    FloorplanAreasLib.clickMaterial(comp, event, material, color, objectData);
    FloorplanAreasLib.mouseOverMaterial(comp, event, material, color, objectData);
    FloorplanAreasLib.redrawArea(comp, material, objectData, floorNr);
    FloorplanAreasLib.changeApartmentType(comp, material, element, oldType, newType);
    FloorplanAreasLib.highlightMaterial(comp, mesh);
    FloorplanAreasLib.highlightMaterialLogic(comp, mesh);
    FloorplanAreasLib.highlightMaterialOver(comp, mesh);
    FloorplanAreasLib.restoreMaterial(comp);
    FloorplanAreasLib.restoreMaterialOver(comp, newMesh);
     */
  });
});
