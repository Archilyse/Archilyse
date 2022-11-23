import { FloorplanEditorComponent } from '../../_shared-components/floorplan/floorplan-editor.component';
import { AreaService } from '../area.service';

export interface FloorplanInterfaceService {
  // On click we select the full unit instead
  highlightUnits?: boolean;
  renderUnits?: boolean;

  uuidToObject;
  idToObject;
  indexToError;

  idAndFloorToArea;
  idToUnit;

  /**
   * User presses a key
   * @param floorplan the FloorplanEditorComponent component instance
   * @param event
   * @param keyCode
   */
  handleKeyDown(floorplan: FloorplanEditorComponent, event, keyCode: string);

  /**
   * User reselases a key
   * @param floorplan the FloorplanEditorComponent component instance
   * @param event
   * @param keyCode
   */
  handleKeyUp(floorplan: FloorplanEditorComponent, event, keyCode: string);

  /**
   * @param floorplan the FloorplanEditorComponent component instance
   */
  subscribeToServices(floorplan: FloorplanEditorComponent);

  /**
   * We define how the areas are rendered
   * @param floorplan the FloorplanEditorComponent component instance
   * @param structure
   */
  analyzeStructureColorAreas(floorplan: FloorplanEditorComponent, structure);

  /**
   * We're drawing a polygon that is an area.
   * @param areaService
   * @param container
   * @param areaSurface
   * @param textSize
   * @param editorScale
   * @param originalObject
   * @param fontThree
   * @param segmentMesh
   * @param zIndex
   */
  drawPolygonsAreas(
    areaService: AreaService,
    container,
    areaSurface: number,
    textSize: number,
    editorScale: number,
    originalObject,
    fontThree,
    segmentMesh,
    zIndex
  );

  /**
   * User clicks in an element
   * @param floorplan the FloorplanEditorComponent component instance
   * @param event
   * @param material
   * @param color
   * @param objectData
   */
  clickMaterialArea(floorplan: FloorplanEditorComponent, event, material, color, objectData);

  /**
   * Click material events - highlight
   * @param floorplan the FloorplanEditorComponent component instance
   * @param mesh
   */
  highlightMaterial(floorplan: FloorplanEditorComponent, mesh);

  /**
   * Click material events - highlight
   * @param floorplan the FloorplanEditorComponent component instance
   */
  restoreMaterial(floorplan: FloorplanEditorComponent);

  /**
   * Mouse over events - restore
   * @param floorplan the FloorplanEditorComponent component instance
   * @param mesh
   */
  highlightMaterialOver(floorplan: FloorplanEditorComponent, mesh);

  /**
   * Mouse over events - restore
   * @param floorplan the FloorplanEditorComponent component instance
   * @param newMesh
   */
  restoreMaterialOver(floorplan: FloorplanEditorComponent, newMesh);
}
