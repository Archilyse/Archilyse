import React from 'react';
import { MdAddCircle, MdWarning } from 'react-icons/md';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import If from '../../utils/react-if';
import { SNAP_POINT, SNAP_SEGMENT } from '../../utils/snap';
import { useMouseCanvasPosition, useSvgPlanTransforms } from '../../hooks/export';
import { MODE_SNAPPING } from '../../constants';
import * as SharedStyle from '../../shared-style';
import { VERSION } from '../../version';
import { objectsMap } from '../../utils/objects-utils';
import { projectActions } from '../../actions/export';
import FooterContentButton from './footer-content-button';
import FooterToggleButton from './footer-toggle-button';

const footerBarStyle = {
  position: 'absolute',
  bottom: 0,
  lineHeight: '14px',
  fontSize: '12px',
  color: SharedStyle.COLORS.white,
  backgroundColor: SharedStyle.SECONDARY_COLOR.alt,
  padding: '3px 1em',
  margin: 0,
  boxSizing: 'border-box',
  cursor: 'default',
  userSelect: 'none',
  zIndex: '9001',
} as any; // Complains about zIndex when using React.CSSProperties interface

export const leftTextStyle = {
  position: 'relative',
  borderRight: '1px solid #FFF',
  float: 'left',
  padding: '0 1em',
  display: 'inline-block',
} as React.CSSProperties;

export const rightTextStyle = {
  position: 'relative',
  borderLeft: '1px solid #FFF',
  float: 'right',
  padding: '0 1em',
  display: 'inline-block',
} as React.CSSProperties;

const coordStyle = {
  display: 'inline-block',
  width: '6em',
  margin: 0,
  padding: 0,
} as React.CSSProperties;

const appMessageStyle = { borderBottom: '1px solid #555', lineHeight: '1.5em' };

const FooterBar = ({ state: globalState, width, height, softwareSignature, projectActions }) => {
  const { zoom } = useSvgPlanTransforms();
  const { x, y } = useMouseCanvasPosition();
  const { mode, errors, warnings, snapMask } = globalState;
  const errorsJsx = errors.map((err, ind) => (
    <div key={ind} style={appMessageStyle}>
      [ {new Date(err.date).toLocaleString()} ] {err.error}
    </div>
  ));
  const errorLableStyle = errors.length ? { color: SharedStyle.MATERIAL_COLORS[500].red } : {};
  const errorIconStyle = errors.length
    ? { transform: 'rotate(45deg)', color: SharedStyle.MATERIAL_COLORS[500].red }
    : { transform: 'rotate(45deg)' };

  const warningsJsx = warnings.map((warn, ind) => (
    <div key={ind} style={appMessageStyle}>
      [ {new Date(warn.date).toLocaleString()} ] {warn.warning}
    </div>
  ));
  const warningLableStyle = warnings.length ? { color: SharedStyle.MATERIAL_COLORS[500].yellow } : {};
  const warningIconStyle = warningLableStyle;

  const updateSnapMask = val => {
    const newSnapMask = {
      ...globalState.snapMask,
      ...val,
    };
    projectActions.toggleSnap(newSnapMask);
  };

  return (
    <div style={{ ...footerBarStyle, width, height }}>
      <If condition={MODE_SNAPPING.includes(mode)}>
        <div style={leftTextStyle}>
          <div title={'Mouse X Coordinate'} style={coordStyle}>
            X : {x.toFixed(3)}
          </div>
          <div title={'Mouse Y Coordinate'} style={coordStyle}>
            Y : {y.toFixed(3)}
          </div>
        </div>

        <div style={leftTextStyle} title={'Scene Zoom Level'}>
          Zoom: {zoom.toFixed(3)}X
        </div>

        <div style={leftTextStyle}>
          <FooterToggleButton
            toggleOn={() => {
              updateSnapMask({ SNAP_POINT: true });
            }}
            toggleOff={() => {
              updateSnapMask({ SNAP_POINT: false });
            }}
            text="Snap PT"
            toggleState={snapMask[SNAP_POINT]}
            title={'Snap to Point'}
          />
          <FooterToggleButton
            toggleOn={() => {
              updateSnapMask({ SNAP_SEGMENT: true });
            }}
            toggleOff={() => {
              updateSnapMask({ SNAP_SEGMENT: false });
            }}
            text="Snap SEG"
            toggleState={snapMask[SNAP_SEGMENT]}
            title={'Snap to Segment'}
          />
        </div>
        <div>
          <FooterToggleButton
            toggleOn={() => projectActions.toggleShowSnapElements()}
            toggleOff={() => projectActions.toggleShowSnapElements()}
            text="Show snap"
            toggleState={globalState.showSnapElements}
            title={'Show snap elements in red while drawing'}
          />
        </div>
      </If>

      {softwareSignature ? (
        <div
          style={rightTextStyle}
          title={
            softwareSignature + (softwareSignature.includes('React-Planner') ? '' : ` using React-Planner ${VERSION}`)
          }
        >
          {softwareSignature}
        </div>
      ) : null}

      <div style={rightTextStyle}>
        <FooterContentButton
          state={globalState}
          icon={MdAddCircle}
          iconStyle={errorIconStyle}
          text={errors.length.toString()}
          textStyle={errorLableStyle}
          title={`Errors [ ${errors.length} ]`}
          titleStyle={errorLableStyle}
          content={[errorsJsx]}
        />
        <FooterContentButton
          state={globalState}
          icon={MdWarning}
          iconStyle={warningIconStyle}
          text={warnings.length.toString()}
          textStyle={warningLableStyle}
          title={`Warnings [ ${warnings.length} ]`}
          titleStyle={warningLableStyle}
          content={[warningsJsx]}
        />
      </div>
    </div>
  );
};

function mapStateToProps(state) {
  state = state['react-planner'];
  return {
    state,
  };
}

const mapDispatchToProps = dispatch => {
  const actions = { projectActions };
  const dispatchToProps = objectsMap(actions, actionNamespace =>
    bindActionCreators(actions[actionNamespace], dispatch)
  );
  return dispatchToProps;
};

export default connect(mapStateToProps, mapDispatchToProps)(FooterBar);
