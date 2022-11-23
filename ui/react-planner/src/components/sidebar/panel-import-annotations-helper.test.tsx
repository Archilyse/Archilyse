import { MOCK_ANNOTATIONS_RESPONSE, serverMocks } from '../../tests/utils/';

import { Background } from '../../types';
import { MOCK_SCENE } from '../../tests/utils';
import { reloadProject } from './panel-import-annotations-helper';

const { buildHandler, ENDPOINTS_PATTERN, server } = serverMocks;

const MOCK_BACKGROUND: Background = { shift: { x: 1, y: 1 }, rotation: 1, width: 1500, height: 1500 };
const MOCK_PLAN_ID = MOCK_ANNOTATIONS_RESPONSE.plan_id;

describe('reloadProject', () => {
  let projectActions;

  beforeAll(() => {
    server.listen();
  });

  afterEach(() => {
    server.resetHandlers();
  });

  afterAll(() => {
    server.close();
  });

  beforeEach(() => {
    projectActions = {
      loadProject: jest.fn(),
      setMode: jest.fn(),
      reGenerateAreas: jest.fn(),
      setProjectHashCode: jest.fn(),
      setValidationErrors: jest.fn(),
      setMustImportAnnotations: jest.fn(),
      setScaleValidated: jest.fn(),
      showSnackbar: jest.fn(),
    };
  });

  it('Imports an annotation and loads the project using the background passed per parameter', async () => {
    server.use(buildHandler(ENDPOINTS_PATTERN.ANNOTATION_PLAN, 'get', { data: MOCK_SCENE }));

    await reloadProject(MOCK_PLAN_ID, projectActions, MOCK_BACKGROUND, false);

    expect(projectActions.loadProject).toBeCalledWith({ ...MOCK_SCENE, background: MOCK_BACKGROUND });
  });

  it('With NO scale validated, imports an annotation and calls all expected project actions', async () => {
    server.use(buildHandler(ENDPOINTS_PATTERN.ANNOTATION_PLAN, 'get', { data: MOCK_SCENE }));

    const currentScaleValidated = false;
    await reloadProject(MOCK_PLAN_ID, projectActions, MOCK_BACKGROUND, currentScaleValidated);

    Object.values(projectActions).forEach(action => {
      expect(action).toBeCalled();
    });
  });

  it('With scale validated, imports an annotation and calls all expected project actions', async () => {
    server.use(buildHandler(ENDPOINTS_PATTERN.ANNOTATION_PLAN, 'get', { data: MOCK_SCENE }));

    const currentScaleValidated = true;
    await reloadProject(MOCK_PLAN_ID, projectActions, MOCK_BACKGROUND, currentScaleValidated);

    const { setScaleValidated, ...restOfActions } = projectActions;

    Object.values(restOfActions).forEach(action => expect(action).toBeCalled());
    expect(setScaleValidated).not.toBeCalled();
  });
});
