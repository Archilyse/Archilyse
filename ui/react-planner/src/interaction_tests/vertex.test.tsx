import { serverMocks } from '../tests/utils/';
import { BEGIN_DRAGGING_VERTEX, END_DRAGGING_VERTEX, UPDATE_DRAGGING_VERTEX } from '../constants';
import Line from '../class/line';
import Layer from '../class/layer';
import Hole from '../class/hole';
import { clickAndDragAMainVertex, setupMocks, setupRedux, setupServer, waitForSceneLoad } from './utils';
import renderReactPlanner from './renderReactPlanner';

const { server } = serverMocks;
setupMocks();

describe('Vertex interaction', () => {
  let props;
  let store;
  beforeAll(() => {
    setupServer(server);
  });

  beforeEach(() => {
    const withActionsHistory = true;
    const setup = setupRedux(withActionsHistory);
    props = setup.props;
    store = setup.store;
  });

  afterEach(() => {
    store.clearActions();
  });

  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };

    return renderReactPlanner(props, store);
  };

  it('Clicking a main vertex should dispatch begin, update and end dragging actions', async () => {
    renderComponent();
    await waitForSceneLoad();

    clickAndDragAMainVertex(store);
    const endDragVertexAction = store.getActions().pop();
    const updateDragVertexAction = store.getActions().pop();
    const beginDragVertexAction = store.getActions().pop();

    expect(beginDragVertexAction.type).toBe(BEGIN_DRAGGING_VERTEX);
    expect(updateDragVertexAction.type).toBe(UPDATE_DRAGGING_VERTEX);
    expect(endDragVertexAction.type).toBe(END_DRAGGING_VERTEX);
  });

  it('Ending dragging a main vertex should call Line.postprocess, Layer.detectAndUpdateAreas', async () => {
    const detectAndUpdateAreasSpy = jest.spyOn(Layer, 'detectAndUpdateAreas');
    const postprocessLineSpy = jest.spyOn(Line, 'postprocess');
    renderComponent();
    await waitForSceneLoad();

    clickAndDragAMainVertex(store);
    expect(detectAndUpdateAreasSpy).toHaveBeenCalled();
    expect(postprocessLineSpy).toHaveBeenCalled();
  });

  it('While dragging a main vertex should call Hole.adjustHolePolygonAfterLineChange', async () => {
    const adjustHolePolygonAfterLineChangeSpy = jest.spyOn(Hole, 'adjustHolePolygonAfterLineChange');
    renderComponent();
    await waitForSceneLoad();

    clickAndDragAMainVertex(store);
    expect(adjustHolePolygonAfterLineChangeSpy).toHaveBeenCalled();
  });
});
