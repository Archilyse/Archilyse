import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { FaAngleDown, FaAngleUp } from 'react-icons/fa';
import * as SharedStyle from '../../shared-style';
import PanelProps from '../../types/PanelProps';

const STYLE_TITLE = {
  fontSize: '11px',
  color: SharedStyle.PRIMARY_COLOR.text_alt,
  padding: '5px 15px 8px 15px',
  backgroundColor: SharedStyle.PRIMARY_COLOR.alt,
  textShadow: '-1px -1px 2px rgba(0, 0, 0, 1)',
  boxShadow: 'inset 0px -3px 19px 0px rgba(0,0,0,0.5)',
  margin: '0px',
  cursor: 'pointer',
};
const STYLE_CONTENT = {
  fontSize: '11px',
  color: SharedStyle.PRIMARY_COLOR.text_alt,
  border: '1px solid #222',
  padding: '0px',
  backgroundColor: SharedStyle.PRIMARY_COLOR.alt,
  textShadow: '-1px -1px 2px rgba(0, 0, 0, 1)',
};

const Panel = (props: PanelProps) => {
  const [opened, setOpened] = useState(props?.opened || false);
  const [hover, setHover] = useState(false);

  const toggleOpen = () => {
    setOpened(!opened);
  };

  const toggleHover = () => {
    setHover(!hover);
  };
  const { name, children } = props;

  return (
    <div
      style={{
        borderTop: '1px solid #222',
        borderBottom: '1px solid #48494E',
        userSelect: 'none',
      }}
    >
      <h3
        style={{
          ...STYLE_TITLE,
          color: hover ? SharedStyle.SECONDARY_COLOR.main : SharedStyle.PRIMARY_COLOR.text_alt,
        }}
        onMouseEnter={() => toggleHover()}
        onMouseLeave={() => toggleHover()}
        onClick={() => toggleOpen()}
      >
        {name}
        {opened ? <FaAngleUp style={{ float: 'right' }} /> : <FaAngleDown style={{ float: 'right' }} />}
      </h3>

      <div style={{ ...STYLE_CONTENT, display: opened ? 'block' : 'none' }}>{children}</div>
    </div>
  );
};

Panel.propTypes = {
  name: PropTypes.string.isRequired,
  opened: PropTypes.bool,
  children: PropTypes.any,
};

export default Panel;
