import React from 'react';
import { connect } from 'react-redux';
import * as SharedStyle from '../../shared-style';
import { MODE_HELP } from '../../constants';
import isScaling from '../../utils/is-scaling';
import BackgroundImage from './backgroundImage';
import Scene from './scene';
import Snap from './snap';
import ValidationErrors from './validationErrors';
import Help from './help';

const guideStyle = {
  stroke: SharedStyle.SECONDARY_COLOR.main,
  strokewidth: '2.5px',
};

const State = ({
  activeSnapElement,
  snapElements,
  showSnapElements,
  mode,
  validationErrors,
  highlightedError,
  sceneHeight,
  sceneWidth,
  guidesHorizontal,
  guidesVertical,
  isScaling,
  showBackgroundOnly,
}) => {
  activeSnapElement = activeSnapElement ? (
    <Snap snap={activeSnapElement} width={sceneWidth} height={sceneHeight} />
  ) : null;
  snapElements = showSnapElements
    ? snapElements.map((snap, id) => <Snap key={id} snap={snap} width={sceneWidth} height={sceneHeight} />)
    : null;

  const displayValidationErrors = validationErrors.length > 0 && !isScaling && !showBackgroundOnly;

  return (
    <g>
      <BackgroundImage />
      <g transform={`translate(0, ${sceneHeight}) scale(1, -1)`} id="svg-drawing-paper">
        {displayValidationErrors && <ValidationErrors errors={validationErrors} highlightedError={highlightedError} />}
        <Scene />
        {Object.entries(guidesHorizontal).map(([hgKey, hgVal]) => (
          <line id={'hGuide' + hgKey} key={hgKey} x1={0} y1={hgVal} x2={sceneWidth} y2={hgVal} style={guideStyle} />
        ))}
        {Object.entries(guidesVertical).map(([vgKey, vgVal]) => (
          <line key={vgKey} x1={vgVal} y1={0} x2={vgVal} y2={sceneHeight} style={guideStyle} />
        ))}
        {activeSnapElement}
        {snapElements}
      </g>
      {mode === MODE_HELP ? <Help /> : null}
    </g>
  );
};

function mapStateToProps(state) {
  state = state['react-planner'];
  const { activeSnapElement, snapElements, showSnapElements, scene, mode, validationErrors, highlightedError } = state;

  const sceneHeight = scene.height;
  const sceneWidth = scene.width;
  const guidesHorizontal = scene.guides.horizontal;
  const guidesVertical = scene.guides.vertical;

  return {
    activeSnapElement,
    snapElements,
    showSnapElements,
    mode,
    validationErrors,
    highlightedError,
    sceneHeight,
    sceneWidth,
    guidesHorizontal,
    guidesVertical,
    isScaling: isScaling(state),
    showBackgroundOnly: state.showBackgroundOnly,
  };
}

export default connect(mapStateToProps)(State);
