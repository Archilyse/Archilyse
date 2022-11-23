import { BEGIN_DRAGGING_VERTEX, END_DRAGGING_VERTEX, UPDATE_DRAGGING_VERTEX } from '../constants';
import { Vertex } from '../class/export';
import { history } from '../utils/export';

export default (state, action) => {
  switch (action.type) {
    case BEGIN_DRAGGING_VERTEX:
      state.sceneHistory = history.historyPush(state.sceneHistory, state.scene);
      return Vertex.beginDraggingVertex(state, action.layerID, action.vertexID, action.x, action.y).updatedState;

    case UPDATE_DRAGGING_VERTEX:
      return Vertex.updateDraggingVertex(state, action.x, action.y).updatedState;

    case END_DRAGGING_VERTEX:
      return Vertex.endDraggingVertex(state, action.x, action.y).updatedState;

    default:
      return state;
  }
};
