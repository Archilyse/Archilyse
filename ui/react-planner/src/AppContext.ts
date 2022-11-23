import { createContext } from 'react';
import { objectsMap } from './utils/objects-utils';
import actions from './actions/export';

// @TODO: Add context type
const AppContext = createContext({
  ...objectsMap(actions, () => {}),
  catalog: {},
  snackbar: {},
});

export default AppContext;
