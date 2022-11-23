import React, { ReactNode, useEffect } from 'react';
import nprogress from 'nprogress';
import { Redirect, Route, BrowserRouter as Router, Switch } from 'react-router-dom';
import { RouteProps } from 'react-router';
import { auth, SnackbarContextProvider } from 'archilyse-ui-components';
import { ErrorBoundary, Layout, RouteChangeSubscriber } from './components';
import {
  Client,
  ClientNew,
  Clients,
  Competition,
  CompetitionConfig,
  CompetitionFeatures,
  CompetitionNew,
  Competitions,
  FloorPlan,
  Home,
  Login,
  ManualSurroundings,
  Pipelines,
  Profile,
  Site,
  SiteNew,
  Sites,
  User,
  UserNew,
  Users,
} from './views';
import { C } from './common';
import { ActionsType, checkAccess } from './common/roles';
import { useBeforeMount } from './common/hooks';
import * as savedRoute from './common/modules/savedRoute';
import 'nprogress/nprogress.css';
import 'archilyse-ui-components/dist/styles.css';
import './app.scss';

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

            <PrivateRoute path="/profile">
              <Profile />
            </PrivateRoute>

            <PrivateRoute path="/pipelines">
              <Pipelines />
            </PrivateRoute>

            <PrivateRoute path="/client/new">
              <ClientNew />
            </PrivateRoute>
            <PrivateRoute path="/client/:id">
              <Client />
            </PrivateRoute>

            <PrivateRoute path="/clients">
              <Clients />
            </PrivateRoute>

            <PrivateRoute path="/user/new">
              <UserNew />
            </PrivateRoute>
            <PrivateRoute path="/user/:id">
              <User />
            </PrivateRoute>
            <PrivateRoute path="/users">
              <Users />
            </PrivateRoute>

            <PrivateRoute path="/site/new">
              <SiteNew />
            </PrivateRoute>
            <PrivateRoute path="/site/:id">
              <Site />
            </PrivateRoute>
            <PrivateRoute path="/sites">
              <Sites />
            </PrivateRoute>

            <PrivateRoute path="/competitions">
              <Competitions />
            </PrivateRoute>
            <PrivateRoute path="/competition/new">
              <CompetitionNew />
            </PrivateRoute>
            <PrivateRoute path="/competition/:id/features">
              <CompetitionFeatures />
            </PrivateRoute>
            <PrivateRoute path="/competition/:id/config">
              <CompetitionConfig />
            </PrivateRoute>
            <PrivateRoute path="/competition/:id">
              <Competition />
            </PrivateRoute>

            <PrivateRoute path="/floor/plan">
              <FloorPlan />
            </PrivateRoute>

            <PrivateRoute path="/manual_surroundings/:id">
              <ManualSurroundings />
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

const PublicRoute = props => {
  useProgressBar();
  return <Route {...props} />;
};

interface PrivateRouteProps extends RouteProps {
  children: ReactNode;
  permission?: ActionsType;
}

const PrivateRoute = ({ children, path, ...rest }: PrivateRouteProps) => {
  useProgressBar();

  const getRender = ({ location }) => {
    if (auth.isAuthenticated()) {
      return checkAccess(path as ActionsType) ? <Layout>{children}</Layout> : <Redirect to={C.URLS.LOGIN()} />;
    }

    return <Redirect to={{ pathname: '/login', state: { from: location } }} />;
  };

  return <Route {...rest} render={getRender} />;
};

export default App;
