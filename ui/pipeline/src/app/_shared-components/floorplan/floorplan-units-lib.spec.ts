import { async, ComponentFixture } from '@angular/core/testing';
import { FloorplanEditorComponent } from './floorplan-editor.component';
import { afterEachFloorplan, beforeEachComponent, beforeEachSetUp } from './floorplan-test-lib';

describe('Floorplan units library', () => {
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

    /** TODO: To be tested:
    FloorplanUnitsLib.clickUnit(comp, objectData);
    FloorplanUnitsLib.findUnit(editorService, unitNumber);
    FloorplanUnitsLib.highlightUnit(comp, unitNumber, floorNr);
    FloorplanUnitsLib.restoreUnitMaterialOver(selectedMeshes, previousMaterials);
    FloorplanUnitsLib.changeApartmentNr(comp, newApartment, floorNr, areaMesh, areaMeshData, manualChanged, floorId);
    FloorplanUnitsLib.drawClientIdText(comp, unitNumber);
    */
  });
});
