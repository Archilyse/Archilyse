import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import Grids from './grids/grids';
import Layer from './layer';

class Scene extends Component {
  render() {
    const { scene } = this.props;
    const { layers } = scene;
    const selectedLayer = layers[scene.selectedLayer];
    return (
      <g>
        <Grids scene={scene} />
        {selectedLayer && <Layer />}
      </g>
    );
  }
}

Scene.propTypes = {
  scene: PropTypes.object.isRequired,
};

function mapStateToProps(state) {
  state = state['react-planner'];
  const { mode, scene } = state;
  return {
    mode,
    scene,
  };
}

export default connect(mapStateToProps)(Scene);
