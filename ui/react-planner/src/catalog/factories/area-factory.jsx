import { area } from '@turf/turf';
import React from 'react';
import * as SharedStyle from '../../shared-style';

export default function AreaFactory(name, info, areaType = 'not_defined') {
  const areaElement = {
    name,
    prototype: 'areas',
    info: {
      ...info,
      visibility: {
        catalog: false,
        layerElementsVisible: false,
      },
    },
    properties: {
      patternColor: {
        label: 'Color',
        type: 'hidden',
        defaultValue: SharedStyle.AREA_MESH_COLOR.unselected,
      },
      areaType: areaType,
    },
    render2D: function (element, layer, scene) {
      const coords = element.coords;
      if (!coords || !coords.length) return null;
      const [areaCoords] = coords;
      if (!areaCoords || !areaCoords.length) return null;
      const polygonPoints = areaCoords.map(([x, y]) => `${x}, ${y}`).join(',');

      let fill = element.selected ? SharedStyle.AREA_MESH_COLOR.selected : SharedStyle.AREA_MESH_COLOR.unselected;
      const fillOpacity = element.selected
        ? SharedStyle.AREA_MESH_OPACITY.selected
        : SharedStyle.AREA_MESH_OPACITY.unselected;

      if (element.isScaleArea) {
        fill = SharedStyle.AREA_MESH_COLOR.scaleArea;
      }

      return <polygon role="presentation" fillOpacity={fillOpacity} fill={fill} points={polygonPoints} />;
    },
  };

  areaElement.properties.areaType = {
    label: 'Area Type',
    type: 'hidden',
    defaultValue: '',
    values: [],
  };

  return areaElement;
}
