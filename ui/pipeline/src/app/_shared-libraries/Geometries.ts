import {
  Mesh,
  Shape,
  Line,
  CircleGeometry,
  MeshPhongMaterial,
  LineBasicMaterial,
  ExtrudeGeometry,
  TextGeometry,
  Geometry,
  Vector3,
} from 'three-full/builds/Three.es.js';
import { COOR_X, COOR_Y } from './SimData';
import { isAnArea } from './EditorConstants';
import { getTextSizeForAreas } from './GeometriesHelper';
import { FloorplanInterfaceService } from '../_services/floorplan/floorplan.interface.service';
import { EditorMath } from './EditorMath';
import { AreaService } from '../_services/area.service';
import { hasOwnNestedProperty } from './Validations';
import { FloorplanIdManager } from '../_services/floorplan/floorplanIdManager';
import { errorMaterial, textMaterial } from './EditorMaterials';

export function drawText(text, container, fontThree, areaSurface, zIndex) {
  const textSize = getTextSizeForAreas(areaSurface);
  const geometry = new TextGeometry(text, {
    size: textSize * 0.4,
    height: 1,
    curveSegments: 1,
    font: fontThree,
    bevelEnabled: false,
  });
  geometry.center();
  const textMesh = new Mesh(geometry, textMaterial);
  textMesh.position.set(0, 0, zIndex + 4);
  container.add(textMesh);
}

/**
 * Draws only the line provided without filling
 * @param container
 * @param footprint
 * @param lineColor
 * @param lineWidth
 * @param zIndex
 */
export function drawGeometries(container, footprint, lineColor, lineWidth, zIndex) {
  const material = new LineBasicMaterial({
    color: lineColor,
    linewidth: lineWidth,
  });

  footprint.coordinates.map(point => {
    const geometry = new Geometry();

    point.forEach(coordinates => {
      geometry.vertices.push(new Vector3(coordinates[COOR_X], coordinates[COOR_Y], 0.1));
    });

    const segment = new Line(geometry, material);
    container.add(segment);
  });
}

/**
 * Adds over the error circle a text with the index of the error so it can be identified
 * @param container
 * @param error
 * @param fontThree
 * @param index
 */
export function drawErrorText(container, error, fontThree, index) {
  const text = new TextGeometry(`${index + 1}`, {
    size: 40,
    height: 1,
    curveSegments: 1,
    font: fontThree,
    bevelEnabled: false,
  });
  text.center();
  return new Mesh(text, textMaterial);
}

/**
 * Draws a circle in the error position, over all the elements with a text with the index
 * @param container
 * @param editorLogic
 * @param error
 * @param fontThree
 * @param index
 */
export function drawError(container, editorLogic: FloorplanInterfaceService, error, fontThree, index) {
  if (hasOwnNestedProperty(error, 'position.coordinates')) {
    const circleSize = 40;

    const geometry = new CircleGeometry(circleSize, circleSize);
    const errorElement = new Mesh(geometry, errorMaterial);
    const textElement = drawErrorText(container, error, fontThree, index);

    container.add(errorElement);
    container.add(textElement);

    const error_zIndex = 5.0;
    const error_text_zIndex = 5.1;
    const errCoor = error.position.coordinates;

    errorElement.position.set(errCoor[COOR_X], errCoor[COOR_Y], error_zIndex);
    textElement.position.set(errCoor[COOR_X], errCoor[COOR_Y], error_text_zIndex);

    FloorplanIdManager.registerError(editorLogic, errorElement, index);
  }
}

/**
 * draws the interior of a Polygon
 * @param container
 * @param areaService
 * @param editorLogic
 * @param editorScale
 * @param originalObject
 * @param objectClass
 * @param polygon
 * @param materialColor
 * @param fontThree
 * @param zIndex
 * @param forceMaterial
 * @param polygonOpacity
 * @param onCreate
 */
export function drawPolygons(
  container,
  areaService: AreaService,
  editorLogic: FloorplanInterfaceService,
  editorScale,
  originalObject,
  objectClass,
  polygon,
  materialColor,
  fontThree,
  zIndex,
  forceMaterial,
  polygonOpacity,
  onCreate
) {
  const extrudeSettings = {
    amount: 0,
    bevelEnabled: false,
    steps: null,
    depth: null,
    bevelThickness: null,
    bevelSize: null,
    bevelOffset: null,
    bevelSegments: null,
  };

  if (polygon) {
    polygon.coordinates.map((d, i) => {
      const shape = new Shape();
      shape.moveTo(...d[0]);

      for (let j = 1; j < d.length; j += 1) {
        shape.lineTo(...d[j]);
      }

      let colorFinal = materialColor;
      if (Array.isArray(materialColor)) {
        colorFinal = materialColor[i % materialColor.length];
      }

      let material;
      if (forceMaterial) {
        material = forceMaterial;
      } else {
        material = new MeshPhongMaterial({
          color: colorFinal,
          emissive: colorFinal,
          transparent: polygonOpacity < 1,
          opacity: polygonOpacity,
        });
      }

      // Extrude documentation and example here:
      // https://threejs.org/docs/#api/en/geometries/ExtrudeGeometry
      const segmentGeometry = new ExtrudeGeometry(shape, extrudeSettings);
      const segmentMesh = new Mesh(segmentGeometry, material);

      container.add(segmentMesh);

      if (fontThree && isAnArea(originalObject.type)) {
        const areaSurface = EditorMath.calculateAreaFromPolygon(polygon);

        const textSize = getTextSizeForAreas(areaSurface);

        editorLogic.drawPolygonsAreas(
          areaService,
          container,
          areaSurface,
          textSize,
          editorScale,
          originalObject,
          fontThree,
          segmentMesh,
          zIndex
        );
      }

      container.position.set(0, 0, zIndex);

      onCreate(segmentMesh, objectClass, i, shape);
    });
  }
}
