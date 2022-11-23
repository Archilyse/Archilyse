import React from 'react';
import { Redirect, Route, RouteProps, BrowserRouter as Router, Switch } from 'react-router-dom';
import { auth, SnackbarContextProvider } from 'archilyse-ui-components';
import { C } from 'Common';
import { ActionsType, checkAccess } from 'Common/roles';
import ErrorBoundary from 'Components/ErrorBoundary';
import { Home, Login, Simulation } from './views';
import 'archilyse-ui-components/dist/styles.css';
import './app.scss';

const App = () => {
  return (
    <SnackbarContextProvider>
      <ErrorBoundary>
        <Router basename={C.URLS.BASE_PATH()}>
          <Switch>
            <Route path="/login">
              <Login />
            </Route>

            <PrivateRoute path="/:id">
              <Simulation />
            </PrivateRoute>

            <PrivateRoute path="/">
              <Home />
            </PrivateRoute>
          </Switch>
        </Router>
      </ErrorBoundary>
    </SnackbarContextProvider>
  );
};

interface PrivateRouteProps extends RouteProps {
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
