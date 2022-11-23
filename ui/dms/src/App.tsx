import React, { ReactNode, useEffect } from 'react';
import nprogress from 'nprogress';
import { Redirect, Route, BrowserRouter as Router, Switch } from 'react-router-dom';
import { RouteProps } from 'react-router';
import { auth, SnackbarContextProvider } from 'archilyse-ui-components';
import { ErrorBoundary, Layout, RouteChangeSubscriber } from './components';
import { ActivateAndResetPassword, DMS, ForgotPassword, Login, Profile } from './views';
import { C } from './common';
import { ActionsType, checkAccess } from './common/roles';
import { getInitialPageUrlByRole } from './common/modules';
import { useBeforeMount } from './common/hooks';
import * as savedRoute from './common/modules/savedRoute';
import 'nprogress/nprogress.css';
import 'archilyse-ui-components/dist/styles.css';
import './app.scss';

const VIEWS = Object.values(C.DMS_VIEWS);

const useProgressBar = () => {
  useEffect(() => {
    nprogress.done();
    return () => nprogress.start();
  });
  return true;
};

const App = () => {
  useBeforeMount(savedRoute.restore);

  return (
    <SnackbarContextProvider>
      <ErrorBoundary>
        <Router basename={C.SERVER_BASENAME}>
          <RouteChangeSubscriber />

          <Switch>
            <PublicRoute path="/login">
              <Login />
            </PublicRoute>

            <PublicRoute path="/password/forgot">
              <ForgotPassword />
            </PublicRoute>
            <PublicRoute path="/password/reset">
              <ActivateAndResetPassword />
            </PublicRoute>

            <PrivateRoute path="/profile">
              <Profile />
            </PrivateRoute>

            <PrivateRoute path={VIEWS}>
              <DMS />
            </PrivateRoute>

            <PrivateRoute path="/">
              <Redirect to={getInitialPageUrlByRole()} />
            </PrivateRoute>
          </Switch>
        </Router>
      </ErrorBoundary>
    </SnackbarContextProvider>
  );
};

const PublicRoute = props => {
  useProgressBar();
  return <Route {...props} />;
};

interface PrivateRouteProps extends RouteProps {
  children: ReactNode;
  permission?: ActionsType;
}

const PrivateRoute = ({ children, location, ...rest }: PrivateRouteProps) => {
  useProgressBar();

  const getRender = ({ location }) => {
    if (auth.isAuthenticated()) {
      return checkAccess(location.pathname as ActionsType) ? (
        <Layout>{children}</Layout>
      ) : (
        <Redirect to={C.URLS.LOGIN()} />
      );
    }

    return <Redirect to={{ pathname: '/login', state: { from: location } }} />;
  };

  return <Route {...rest} render={getRender} />;
};

export default App;
