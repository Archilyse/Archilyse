import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import * as SharedStyle from '../../shared-style';
import { useMouseCanvasPosition, useSvgPlanTransforms } from '../../hooks/export';

function RulerY(props) {
  const { zoom, transformY } = useSvgPlanTransforms();
  const zeroTopPosition = props.sceneHeight * zoom + transformY;
  const { y: mouseY } = useMouseCanvasPosition();
  const elementH = props.unitPixelSize * zoom;

  const elementStyle = {
    width: '8px',
    borderBottom: '1px solid ' + props.fontColor,
    paddingBottom: '0.2em',
    fontSize: '10px',
    height: elementH,
    textOrientation: 'upright',
    writingMode: 'vertical-lr',
    letterSpacing: '-2px',
    textAlign: 'right',
  };

  const insideElementsStyle = {
    height: '20%',
    width: '100%',
    textOrientation: 'upright',
    writingMode: 'vertical-lr',
    display: 'inline-block',
    letterSpacing: '-2px',
    textAlign: 'right',
  };

  const rulerStyle = {
    backgroundColor: props.backgroundColor,
    height: props.height,
    width: '100%',
    color: props.fontColor,
  };

  const markerStyle = {
    position: 'absolute',
    top: zeroTopPosition - mouseY * zoom - 6.5 || 0,
    left: 8,
    width: 0,
    height: 0,
    borderTop: '5px solid transparent',
    borderBottom: '5px solid transparent',
    borderLeft: '8px solid ' + props.markerColor,
    zIndex: 9001,
  };

  const rulerContainer = {
    position: 'absolute',
    width: '100%',
    display: 'grid',
    gridRowGap: '0',
    gridColumnGap: '0',
    gridTemplateColumns: '100%',
    grdAutoRows: `${elementH}px`,
    paddingLeft: '5px',
  };

  const positiveRulerContainer = {
    ...rulerContainer,
    top: zeroTopPosition - props.positiveUnitsNumber * elementH || 0,
    height: props.positiveUnitsNumber * elementH,
  };

  const negativeRulerContainer = {
    ...rulerContainer,
    top: zeroTopPosition + props.negativeUnitsNumber * elementH || 0,
    height: props.negativeUnitsNumber * elementH,
  };

  const positiveDomElements = [];

  if (elementH <= 200) {
    for (let x = 1; x <= props.positiveUnitsNumber; x++) {
      positiveDomElements.push(
        <div key={x} style={{ ...elementStyle, gridColumn: 1, gridRow: x }}>
          {elementH > 30 ? (props.positiveUnitsNumber - x) * 100 : ''}
        </div>
      );
    }
  } else if (elementH > 200) {
    for (let x = 1; x <= props.positiveUnitsNumber; x++) {
      const val = (props.positiveUnitsNumber - x) * 100;
      positiveDomElements.push(
        <div key={x} style={{ ...elementStyle, gridColumn: 1, gridRow: x }}>
          <div style={insideElementsStyle}>{val + 4 * 20}</div>
          <div style={insideElementsStyle}>{val + 3 * 20}</div>
          <div style={insideElementsStyle}>{val + 2 * 20}</div>
          <div style={insideElementsStyle}>{val + 1 * 20}</div>
          <div style={insideElementsStyle}>{val}</div>
        </div>
      );
    }
  }

  return (
    <div style={rulerStyle}>
      <div id="verticalMarker" style={markerStyle}></div>
      <div id="negativeRuler" style={negativeRulerContainer}></div>
      <div id="positiveRuler" style={positiveRulerContainer}>
        {positiveDomElements}
      </div>
    </div>
  );
}

RulerY.propTypes = {
  unitPixelSize: PropTypes.number.isRequired,
  height: PropTypes.number.isRequired,
  backgroundColor: PropTypes.string,
  fontColor: PropTypes.string,
  markerColor: PropTypes.string,
};

RulerY.defaultProps = {
  positiveUnitsNumber: 50,
  negativeUnitsNumber: 50,
  backgroundColor: SharedStyle.PRIMARY_COLOR.main,
  fontColor: SharedStyle.COLORS.white,
  markerColor: SharedStyle.SECONDARY_COLOR.main,
};

function mapStateToProps(state) {
  state = state['react-planner'];
  const sceneHeight = state.scene.height;
  return {
    sceneHeight,
  };
}

export default connect(mapStateToProps)(RulerY);
