import React from 'react';
import PropTypes from 'prop-types';
import Panel from '../panel';
import {
  MODE_2D_PAN,
  MODE_2D_ZOOM_IN,
  MODE_2D_ZOOM_OUT,
  MODE_DRAGGING_HOLE,
  MODE_DRAGGING_ITEM,
  MODE_DRAGGING_VERTEX,
  MODE_DRAWING_HOLE,
  MODE_DRAWING_ITEM,
  MODE_DRAWING_LINE,
  MODE_FITTING_IMAGE,
  MODE_IDLE,
  MODE_ROTATING_ITEM,
  MODE_UPLOADING_IMAGE,
  MODE_WAITING_DRAWING_LINE,
} from '../../../constants';
import ElementEditor from './element-editor';

export default function PanelElementEditor({ state }) {
  const { scene, mode } = state;

  if (
    ![
      MODE_IDLE,
      MODE_2D_ZOOM_IN,
      MODE_2D_ZOOM_OUT,
      MODE_2D_PAN,
      MODE_WAITING_DRAWING_LINE,
      MODE_DRAWING_LINE,
      MODE_DRAWING_HOLE,
      MODE_DRAWING_ITEM,
      MODE_DRAGGING_VERTEX,
      MODE_DRAGGING_ITEM,
      MODE_DRAGGING_HOLE,
      MODE_ROTATING_ITEM,
      MODE_UPLOADING_IMAGE,
      MODE_FITTING_IMAGE,
    ].includes(mode)
  )
    return null;

  const componentRenderer = (element, layer) => {
    return (
      <Panel key={element.id} name={`Properties: [${element.type}]`} opened={true}>
        <div style={{ padding: '5px 15px' }}>
          <ElementEditor element={element} layer={layer} />
        </div>
      </Panel>
    );
  };

  const layerRenderer = layer => {
    const allElems = [].concat(layer.lines, layer.holes, layer.areas, layer.items).map(Object.values).flat();
    const selectedElems = allElems.filter(element => element.selected);
    return selectedElems.map(element => componentRenderer(element, layer));
  };

  const layersFetched = Object.keys(scene.layers).length !== 0;

  const layers = Object.values(scene.layers);
  return layersFetched ? <div>{layers.map(layerRenderer)}</div> : null;
}

PanelElementEditor.propTypes = {
  state: PropTypes.object.isRequired,
};
