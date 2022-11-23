import { fireEvent, screen } from '@testing-library/react';
import { serverMocks } from '../tests/utils/';
import { KEYBOARD_KEYS } from '../constants';
import MyCatalog from '../catalog-elements/mycatalog';
import { selectFromCatalog, setupMocks, setupRedux, setupServer, waitForSceneLoad } from './utils';
import renderReactPlanner from './renderReactPlanner';

const { server } = serverMocks;

setupMocks();

describe('Catalog interaction', () => {
  let props;
  let store;

  beforeAll(() => {
    setupServer(server);
  });

  beforeEach(() => {
    const setup = setupRedux();
    props = setup.props;
    store = setup.store;
  });

  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps, store };
    return renderReactPlanner(props, store);
  };

  const catalogNames: string[] = Object.values(MyCatalog.elements)
    .filter((e: any) => e.info.toolbarIcon && Boolean(!e.info.visibility || e.info?.visibility?.catalog))
    .map((element: any) => element.info.title);

  it('Toggles the catalog pressing "l"', async () => {
    const { container } = renderComponent();

    // Show the catalog
    fireEvent.keyDown(container, { key: KEYBOARD_KEYS.L });
    expect(screen.getByTestId('catalog-toolbar')).toBeInTheDocument();
    // Hide it
    fireEvent.keyDown(container, { key: KEYBOARD_KEYS.L });
    expect(screen.queryByTestId('catalog-toolbar')).not.toBeInTheDocument();
  });
  const TEST_CASES: any = catalogNames.map(element => [element]);
  it.each(TEST_CASES)('Can select %s', async title => {
    const { container } = renderComponent();
    await waitForSceneLoad();
    await selectFromCatalog(container, title);
  });
});
