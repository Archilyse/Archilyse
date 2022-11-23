import { FloorplanInterfaceService } from '../../_services/floorplan/floorplan.interface.service';
import { FloorplanEditorComponent } from './floorplan-editor.component';
import { app_declarations } from '../../app.declarations';
import { app_imports } from '../../app.imports';
import { EditorConstants } from '../../_shared-libraries/EditorConstants';
import { TestingConstants } from '../../_shared-libraries/TestingConstants';
import { ComponentFixture, TestBed } from '@angular/core/testing';
/**
 *  Mock  floorplan service for testing
 */
export class FloorplanTestService implements FloorplanInterfaceService {
  idToObject;
  uuidToObject;
  idAndFloorToArea;
  idToUnit;
  indexToError;

  analyzeStructureColorAreas(floorplan: FloorplanEditorComponent, structure) {}

  clickMaterialArea(floorplan: FloorplanEditorComponent, event, material, color, objectData) {}

  drawPolygonsAreas(
    areaService,
    container,
    areaSurface: number,
    textSize: number,
    editorScale: number,
    originalObject,
    fontThree,
    segmentMesh,
    zIndex
  ) {}

  handleKeyDown(floorplan: FloorplanEditorComponent, event, keyCode: string) {}

  handleKeyUp(floorplan: FloorplanEditorComponent, event, keyCode: string) {}

  highlightMaterial(floorplan: FloorplanEditorComponent, mesh) {}

  highlightMaterialOver(floorplan: FloorplanEditorComponent, mesh) {}

  restoreMaterial(floorplan: FloorplanEditorComponent) {}

  restoreMaterialOver(floorplan: FloorplanEditorComponent, newMesh) {}

  subscribeToServices(floorplan: FloorplanEditorComponent) {}
}

export function beforeEachSetUp() {
  TestBed.configureTestingModule({
    declarations: [...app_declarations],
    imports: [...app_imports],
    providers: [FloorplanEditorComponent],
  }).compileComponents();
}

export function beforeEachComponent() {
  const fixture: ComponentFixture<FloorplanEditorComponent> = TestBed.createComponent(FloorplanEditorComponent);
  const comp: FloorplanEditorComponent = fixture.componentInstance;

  // Default values to test
  comp.cameraToKeep = null;
  comp.selectedByDefault = null;
  comp.colorIndexes = EditorConstants.COLORS_HEX;
  comp.addFurniture = false;

  comp.SCALE = 1;
  comp.areaTypes = TestingConstants.areaTypes;
  comp.model = TestingConstants.brooksModel;
  comp.logic = new FloorplanTestService();

  fixture.detectChanges();
  return {
    comp,
    fixture,
  };
}

export function afterEachFloorplan(fixture) {
  document.body.removeChild(fixture.debugElement.nativeElement);
}
