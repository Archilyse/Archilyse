import React from 'react';
import { connect } from 'react-redux';
import { MODE_COPY_PASTE, MODE_RECTANGLE_TOOL } from '../../constants';
import MyCatalog from '../../catalog-elements/mycatalog';
import isScaling from '../../utils/is-scaling';
import Vertex from './vertex';
import Line from './line';
import Item from './item';
import Area from './area';
import CopyPasteSelection from './copyPasteSelection';
import RectangleToolSelection from './rectangleToolSelection';

function Layer({ layer, scene, mode, scaleTool, isScaling, showBackgroundOnly }) {
  const { unit } = scene;
  const { lines, areas, vertices, items, opacity } = layer;

  const innerAreas = Object.values(areas).filter(a => a.coords.length == 1);
  const outerAreas = Object.values(areas).filter(a => a.coords.length > 1);
  const areasOrdered = outerAreas.concat(innerAreas);

  if (showBackgroundOnly) {
    // Display only selected (e.g. being drawn) annotations
    return (
      <g opacity={opacity} data-testid="layer-container">
        {Object.values(lines)
          .filter(line => line.selected)
          .map(line => (
            <Line key={line.id} layer={layer} line={line} scene={scene} catalog={MyCatalog} />
          ))}
        {Object.values(items)
          .filter(item => item.selected)
          .map(item => (
            <Item key={item.id} layer={layer} item={item} scene={scene} mode={mode} catalog={MyCatalog} />
          ))}
        {Object.values(vertices)
          .filter(v => v.selected)
          .map(vertex => (
            <Vertex key={vertex.id} layer={layer} vertex={vertex} isScaling={isScaling} />
          ))}
      </g>
    );
  }
  return (
    <g opacity={opacity} data-testid="layer-container">
      {areasOrdered.map(area => (
        <Area
          key={area.id}
          mode={mode}
          layer={layer}
          area={area}
          unit={unit}
          catalog={MyCatalog}
          scale={scene.scale}
          scaleTool={scaleTool}
        />
      ))}
      {Object.values(lines).map(line => (
        <Line key={line.id} layer={layer} line={line} scene={scene} catalog={MyCatalog} />
      ))}
      {Object.values(items).map(item => (
        <Item key={item.id} layer={layer} item={item} scene={scene} mode={mode} catalog={MyCatalog} />
      ))}
      {Object.values(vertices)
        .filter(v => v.selected)
        .map(vertex => (
          <Vertex key={vertex.id} layer={layer} vertex={vertex} isScaling={isScaling} />
        ))}

      {mode === MODE_COPY_PASTE && <CopyPasteSelection />}
      {mode === MODE_RECTANGLE_TOOL && <RectangleToolSelection />}
    </g>
  );
}

function mapStateToProps(state) {
  state = state['react-planner'];
  const { mode, scene, scaleTool } = state;
  const { layers } = scene;
  const selectedLayer = layers[scene.selectedLayer];
  return {
    mode,
    scene,
    scaleTool,
    layer: selectedLayer,
    isScaling: isScaling(state),
    showBackgroundOnly: state.showBackgroundOnly,
  };
}

export default connect(mapStateToProps)(Layer);
