import React from 'react';
import { Redirect, Route, RouteProps, BrowserRouter as Router, Switch } from 'react-router-dom';
import { auth, SnackbarContextProvider } from 'archilyse-ui-components';
import { ErrorBoundary } from './components';
import { Competition, Competitions, Login, QA } from './views';
import { C } from './common';
import 'archilyse-ui-components/dist/styles.css';
import './app.scss';
import { ActionsType, checkAccess } from './common/roles';

const App = () => {
  return (
    <SnackbarContextProvider>
      <ErrorBoundary>
        <Router basename={C.SERVER_BASENAME}>
          <Switch>
            <Route path="/login">
              <Login />
            </Route>
            <PrivateRoute path="/qa/:siteId">
              <QA />
            </PrivateRoute>
            <PrivateRoute path="/competitions">
              <Competitions />
            </PrivateRoute>
            <PrivateRoute path="/competition/:id">
              <Competition />
            </PrivateRoute>
            <PrivateRoute path="/">
              <Competitions />
            </PrivateRoute>
          </Switch>
        </Router>
      </ErrorBoundary>
    </SnackbarContextProvider>
  );
};

interface PrivateRouteProps extends RouteProps {
  path: string;
  children: React.ReactNode;
  permission?: ActionsType;
}

const PrivateRoute = ({ children, path, ...rest }: PrivateRouteProps) => {
  const getRender = ({ location }) => {
    if (auth.isAuthenticated()) {
      return checkAccess(path as ActionsType) ? children : <Redirect to={C.URLS.LOGIN()} />;
    }

    return <Redirect to={{ pathname: '/login', state: { from: location } }} />;
  };

  return <Route {...rest} render={getRender} />;
};

export default App;
