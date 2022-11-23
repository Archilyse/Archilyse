import React, { Component } from 'react';
import PropTypes from 'prop-types';
import * as SharedStyle from '../../shared-style';

//http://www.cssportal.com/css-tooltip-generator/

// @TODO: To functional component & to tsx
const STYLE = {
  width: '30px',
  height: '30px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  marginBottom: '10px',
  fontSize: '25px',
  position: 'relative',
  cursor: 'pointer',
  background: 'none',
  border: 'none',
};

const STYLE_TOOLTIP = {
  position: 'absolute',
  width: '160px',
  color: SharedStyle.COLORS.white,
  background: SharedStyle.COLORS.black,
  height: '30px',
  lineHeight: '30px',
  textAlign: 'center',
  visibility: 'visible',
  borderRadius: '6px',
  opacity: '0.8',
  left: '100%',
  top: '50%',
  marginTop: '-15px',
  marginLeft: '15px',
  zIndex: '999',
  fontSize: '12px',
};

const STYLE_TOOLTIP_PIN = {
  position: 'absolute',
  top: '50%',
  right: '100%',
  marginTop: '-8px',
  width: '0',
  height: '0',
  borderRight: '8px solid #000000',
  borderTop: '8px solid transparent',
  borderBottom: '8px solid transparent',
};

export default class ToolbarButton extends Component {
  constructor(props, context) {
    super(props, context);
    this.state = { active: false };
  }

  render() {
    const { state, props } = this;
    const { active, ...buttonProps } = props;
    const color = active || state.active ? SharedStyle.SECONDARY_COLOR.icon : SharedStyle.PRIMARY_COLOR.icon;

    return (
      <button
        className="toolbar-button"
        style={STYLE}
        onMouseOver={event => this.setState({ active: true })}
        onMouseOut={event => this.setState({ active: false })}
        onClick={!buttonProps.disabled && props.onClick}
        {...buttonProps}
      >
        <div style={{ color }}>{props.children}</div>

        {state.active && props.tooltip ? (
          <div style={STYLE_TOOLTIP}>
            <span style={STYLE_TOOLTIP_PIN} />
            {props.tooltip}
            {props.shortcut && <b>-"{props.shortcut}"</b>}
          </div>
        ) : null}
      </button>
    );
  }
}

ToolbarButton.propTypes = {
  active: PropTypes.bool.isRequired,
  tooltip: PropTypes.string,
  onClick: PropTypes.func,
};
