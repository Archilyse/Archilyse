import { Layer } from '../class/export';
import { history } from '../utils/export';
import { SELECT_LAYER } from '../constants';

export default (state, action) => {
  state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);

  switch (action.type) {
    case SELECT_LAYER:
      return Layer.select(state, action.layerID).updatedState;

    default:
      return state;
  }
};
