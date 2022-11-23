import 'core-js/stable';
import 'regenerator-runtime/runtime';
import React from 'react';
import ContainerDimensions from 'react-container-dimensions';
import { auth, SnackbarContextProvider } from 'archilyse-ui-components';
import { Redirect, Route, BrowserRouter as Router, Switch } from 'react-router-dom';
import thunk from 'redux-thunk';
import { applyMiddleware, compose, createStore } from 'redux';
import { createLogger } from 'redux-logger';
import { Provider } from 'react-redux';

import { Models as PlannerModels, reducer as PlannerReducer, ReactPlanner } from './export'; //react-planner
import PlannerPlugins from './plugins/export';
import * as ReactPlannerComponents from './components/export';
import * as ReactPlannerConstants from './constants';
import { SentryInit } from './SentryInit';
import cloneDeep from './utils/clone-deep';

const { Login } = ReactPlannerComponents;
const { URLS, ROLES, SERVER_BASENAME } = ReactPlannerConstants;

const isProduction = window.location.protocol === 'https:' && process.env.NODE_ENV === 'production';

//define state
const AppState = {
  'react-planner': new PlannerModels.State(),
};

//define reducer
const reducer = (state, action) => {
  state = state || cloneDeep(AppState);
  state = PlannerReducer(state['react-planner'], action);
  state = {
    'react-planner': state,
  };
  return state;
};

const blackList = isProduction === true ? [] : ['UPDATE_2D_CAMERA'];

if (!isProduction) {
  console.info('Environment is in development and these actions will be blacklisted', blackList);
}

const devTools = // @ts-ignore
  !isProduction && window.__REDUX_DEVTOOLS_EXTENSION__ // @ts-ignore
    ? window.__REDUX_DEVTOOLS_EXTENSION__({
        features: {
          pause: true, // start/pause recording of dispatched actions
          lock: true, // lock/unlock dispatching actions and side effects
          persist: true, // persist states on page reloading
          export: true, // export history of actions in a file
          import: 'custom', // import history of actions from a file
          jump: true, // jump back and forth (time travelling)
          skip: true, // skip (cancel) actions
          reorder: true, // drag and drop actions in the history list
          dispatch: true, // dispatch custom actions or action creators
          test: true, // generate tests for the selected actions
        },
        actionsBlacklist: blackList,
        maxAge: 999999,
      })
    : f => f;

const logger = createLogger({
  collapsed: true,
  stateTransformer: state => {
    return state;
  },
});
const middlewares = isProduction ? [thunk] : [thunk, logger];
//init store
const store = createStore(reducer, null, compose(applyMiddleware(...middlewares), devTools));

const plugins = [PlannerPlugins.Keyboard(), PlannerPlugins.ConsoleDebugger()];

const PublicRoute = props => <Route {...props} />;

const PrivateRoute = ({ children, path, ...rest }) => {
  const getRender = ({ location }) => {
    if (auth.isAuthenticated()) {
      const canAccessEditor = auth.hasValidRole([ROLES.ADMIN, ROLES.TEAMMEMBER, ROLES.TEAMLEADER]);
      return canAccessEditor ? children : <Redirect to={URLS.HOME()} />;
    }
    return <Redirect to={{ pathname: URLS.LOGIN(), state: { from: location } }} />;
  };

  return <Route {...rest} render={getRender} />;
};

// initialize Sentry and attach redux state on error
SentryInit({
  isProduction,
  store,
});

const App = () => (
  <Provider store={store}>
    <ContainerDimensions>
      {({ width, height }) => (
        <Router basename={SERVER_BASENAME}>
          <Switch>
            <PublicRoute path="/login">
              <SnackbarContextProvider>
                <Login />
              </SnackbarContextProvider>
            </PublicRoute>
            <PrivateRoute path="/:id">
              <ReactPlanner
                width={width}
                height={height}
                plugins={plugins}
                store={store}
                stateExtractor={state => state['react-planner']}
              />
            </PrivateRoute>
            <PrivateRoute path="/">
              <h2 id="home-header">
                Welcome to Archilyse Editor v2, please introduce a url with a plan id like {"'"}/:id{"'"}
              </h2>
            </PrivateRoute>
          </Switch>
        </Router>
      )}
    </ContainerDimensions>
  </Provider>
);

export default App;
