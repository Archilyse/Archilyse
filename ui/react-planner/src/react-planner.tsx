import React, { Component } from 'react';
import { auth, extractError } from 'archilyse-ui-components';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';
import { withRouter } from 'react-router';
import actions from './actions/export';
import { objectsMap } from './utils/objects-utils';
import { CatalogToolbar, Content, FooterBarComponents, Sidebar, Toolbar } from './components/export';
import { VERSION } from './version';
import SnackbarContainer from './components/snackbar/snackbar';
import {
  INITIAL_BACKGROUND_HEIGHT,
  INITIAL_BACKGROUND_WIDTH,
  INITIAL_SCENE_WIDTH,
  MODE_IMPORT_ANNOTATIONS,
  REQUEST_STATUS_BY_ACTION,
  RequestStatusType,
  SNACKBAR_DURATION_FOREVER,
} from './constants';
import getImgDimensions from './utils/get-img-dimensions';
import { getDownScaledImage } from './utils/get-downscaled-img';
import isScaling from './utils/is-scaling';
import needsFloorScales from './needs-floor-scales';
import './styles/export';
import MyCatalog from './catalog-elements/mycatalog';
import { ProviderMetrics } from './providers';

const { FooterBar } = FooterBarComponents;

export const mustImportAnnotations = (project, plan, siteEnforcesMasterPlan): boolean => {
  const noAnnotations = !project || !project.data;
  const isNotMasterPlan = !plan || !plan.is_masterplan;
  return siteEnforcesMasterPlan && noAnnotations && isNotMasterPlan;
};

const toolbarW = 50;
const sidebarW = 300;
const footerBarH = 20;

const wrapperStyle = {
  display: 'flex',
  flexFlow: 'row nowrap',
};

const blockInteractionStyle = {
  opacity: '0.5',
  zIndex: '100',
  overflow: 'visible',
  pointerEvents: 'none',
};

type ReactPlannerProps = {
  plugins: Function[];
  width: number;
  height: number;
  isSaving: boolean;
  isPredicting: boolean;
  stateExtractor: (state) => {};
  customContents: object;
  softwareSignature: string;
  state: any;
  match: any; // @TODO
  projectActions: any;
  planActions: any;
  store: any;
};

type FloorplanDimensions = {
  width: number;
  height: number;
};

class ReactPlanner extends Component<ReactPlannerProps, any> {
  floorplanDimensions: FloorplanDimensions = {
    width: INITIAL_BACKGROUND_WIDTH,
    height: INITIAL_BACKGROUND_HEIGHT,
  };

  constructor(props) {
    super(props);

    this.state = {
      snackbar: { open: false, message: null },
    };

    this.showSnackbar = this.showSnackbar.bind(this);
    this.closeSnackbar = this.closeSnackbar.bind(this);
  }

  showSnackbar({ message, severity, duration }) {
    this.props.projectActions.showSnackbar({ snackbar: { open: true, message, severity, duration } });
  }

  closeSnackbar() {
    this.props.projectActions.closeSnackbar();
  }

  showSnackbarError(errorMessage) {
    this.props.projectActions.showSnackbar({
      message: errorMessage,
      severity: 'error',
      duration: SNACKBAR_DURATION_FOREVER,
    });
  }

  showSnackbarInfo(infoMessage) {
    this.props.projectActions.showSnackbar({
      message: infoMessage,
      severity: 'info',
      duration: SNACKBAR_DURATION_FOREVER,
    });
  }

  async fetchFloorScalesIfNeeded(state, planActions) {
    const planId = this.props.match.params.id;
    const { siteStructure, floorScales } = state;
    const requestStatus = state.requestStatus[REQUEST_STATUS_BY_ACTION.FETCH_FLOOR_SCALES];

    if (needsFloorScales({ isScaling: isScaling(state), floorScales, siteStructure, requestStatus })) {
      await planActions.fetchFloorScales(planId, siteStructure);
    }
  }

  async setInitialBackgroundAndScene({ width, height }) {
    const { projectActions } = this.props;
    projectActions.setBackgroundDimensions({ width, height });
    projectActions.setSceneDimensions({ width, height });
  }

  applyFloorplanDimensionsIfNecessary(project) {
    if (!project || !project.data) return;
    const { width, height } = this.floorplanDimensions;
    const { projectActions } = this.props;

    const initialBackgroundWidth =
      !project.data.background ||
      !project.data.background.width ||
      (project.data.background && project.data.background.width === INITIAL_BACKGROUND_WIDTH);
    if (initialBackgroundWidth) {
      projectActions.setBackgroundDimensions({ width, height });
    }

    const initialSceneWidth = !project.data.width || (project.data && project.data.width === INITIAL_SCENE_WIDTH);
    if (initialSceneWidth) {
      projectActions.setSceneDimensions({ width, height });
    }
  }

  async loadFloorplanImage() {
    const planId = this.props.match.params.id;
    const { planActions } = this.props;
    try {
      const floorplanImgData = await planActions.fetchFloorplan(planId);
      const { width, height, originalImgElem } = await getImgDimensions(floorplanImgData.payload);
      const imgBlob: Blob = await getDownScaledImage({ originalImgElem, imgBlob: floorplanImgData.payload });
      planActions.fulfilledFloorplan(imgBlob);
      this.setInitialBackgroundAndScene({ width, height });
      planActions.setFloorplanDimensions({ width, height });
      this.floorplanDimensions = { width, height };
    } catch (error) {
      this.showSnackbarError(`Error fetching floorplan image: ${extractError(error)}`);
    }
  }

  async loadAnnotations(plan, siteEnforcesMasterPlan) {
    const planId = this.props.match.params.id;
    const { projectActions } = this.props;

    try {
      const project = await projectActions.getProjectAsync(planId);
      if (mustImportAnnotations(project, plan, siteEnforcesMasterPlan)) {
        this.showSnackbarInfo('Please import annotations to start');
        projectActions.setMustImportAnnotations(true);
        projectActions.setMode(MODE_IMPORT_ANNOTATIONS);
      } else if (!project.data || !project.data.scale) {
        this.showSnackbarInfo('Plan without scale, please set it by clicking two points or drawing a polygon');

        projectActions.enableScaling();
      }
      if (project.errors) {
        projectActions.setValidationErrors(project.errors);
      }
      // To be compatible with old plans that were not created from react planner origally, we are always
      // recreating the areas
      projectActions.reGenerateAreas();
      projectActions.setAnnotationFinished(Boolean(project?.annotation_finished));
      projectActions.setScaleValidated(Boolean(project?.data?.scale));
      projectActions.setProjectHashCode();
      this.applyFloorplanDimensionsIfNecessary(project);
    } catch (error) {
      const newPlan = error.response?.status === 404;
      if (newPlan) {
        if (mustImportAnnotations({}, plan, siteEnforcesMasterPlan)) {
          this.showSnackbarInfo('Please import annotations to start');
          projectActions.setMustImportAnnotations(true);
          projectActions.setMode(MODE_IMPORT_ANNOTATIONS);
        } else {
          this.showSnackbarInfo('New plan, please set the scale by drawing a line or an area');
          projectActions.enableScaling();
        }
      } else {
        this.showSnackbarError(`Error fetching annotations: ${extractError(error)}`);
      }
    }
  }

  async loadPlanInfo() {
    const planId = this.props.match.params.id;
    const { projectActions, planActions } = this.props;

    try {
      const plan = await projectActions.getPlanInfoAsync(planId);
      planActions.fetchAvailableAreaTypes(plan);
      const { payload } = await planActions.fetchSiteStructure(plan);
      return { plan, siteEnforcesMasterPlan: payload?.rawStructure?.enforce_masterplan };
    } catch (error) {
      this.showSnackbarError(`Error fetching plan: ${extractError(error)}`);
    }
  }

  initPluginsAndCatalog() {
    const { projectActions, stateExtractor, plugins, store } = this.props;
    plugins.forEach(plugin => plugin(store, stateExtractor));
    projectActions.initCatalog(MyCatalog);
  }

  loadMetrics() {
    const { group_id } = auth.getUserInfo();
    ProviderMetrics.initMetadata({ group_id, plan_id: Number(this.props.match.params.id) });
    ProviderMetrics.trackPageView();
  }

  async loadInitialData() {
    await this.loadFloorplanImage();
    const { plan, siteEnforcesMasterPlan } = (await this.loadPlanInfo()) || {};
    if (!plan) {
      this.showSnackbarError(`Could not find a plan for id: ${this.props.match.params.id}`);
      return;
    }
    await this.loadAnnotations(plan, siteEnforcesMasterPlan);
  }

  async componentDidMount() {
    this.loadMetrics();
    this.initPluginsAndCatalog();
    this.loadInitialData();
  }

  async componentDidUpdate(prevProps: Readonly<ReactPlannerProps>, prevState: Readonly<any>) {
    const { stateExtractor, state, planActions } = this.props;
    const plannerState: any = stateExtractor(state);
    this.fetchFloorScalesIfNeeded(plannerState, planActions);
  }

  render() {
    const { width, height, state, stateExtractor, ...props } = this.props;

    const contentW = width - toolbarW - sidebarW;
    const toolbarH = height - footerBarH;
    const contentH = height - footerBarH;
    const sidebarH = height - footerBarH;

    const extractedState: any = stateExtractor(state);

    const overlayStyle = this.props.isSaving || this.props.isPredicting ? { ...blockInteractionStyle } : {};
    return (
      <>
        <div style={{ ...wrapperStyle, ...overlayStyle, height }}>
          <Toolbar width={toolbarW} height={toolbarH} />
          {extractedState.catalogToolbarOpened && <CatalogToolbar width={toolbarW} height={toolbarH} />}
          <Content width={contentW} height={contentH} mode={extractedState.mode} />
          <Sidebar
            width={sidebarW}
            height={sidebarH}
            state={extractedState}
            stateExtractor={stateExtractor}
            {...props}
          />
          <FooterBar width={width} height={footerBarH} {...props} />
        </div>

        <SnackbarContainer />
      </>
    );
  }

  static defaultProps = {
    plugins: [],
    softwareSignature: `React-Planner ${VERSION}`,
    customContents: {},
  };
}

function mapStateToProps(reduxState) {
  const requestSavingStatus =
    reduxState['react-planner'].requestStatus?.[REQUEST_STATUS_BY_ACTION.SAVE_PLAN_ANNOTATIONS];
  const isSaving = requestSavingStatus?.status === RequestStatusType.PENDING;

  const requestPredictionStatus = reduxState['react-planner'].requestStatus?.[REQUEST_STATUS_BY_ACTION.GET_PREDICTION];

  const isPredicting = requestPredictionStatus?.status === RequestStatusType.PENDING;
  return {
    isSaving,
    isPredicting,
    state: reduxState,
  };
}

function mapDispatchToProps(dispatch) {
  return objectsMap(actions, actionNamespace => bindActionCreators(actions[actionNamespace], dispatch));
}

export default connect(mapStateToProps, mapDispatchToProps)(withRouter(ReactPlanner));
