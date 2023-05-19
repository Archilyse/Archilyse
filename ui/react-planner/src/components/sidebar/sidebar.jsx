import React from 'react';
import PropTypes from 'prop-types';
import { getUserRoles } from 'archilyse-ui-components';
import * as SharedStyle from '../../shared-style';

import { MODE_COPY_PASTE, MODE_IMPORT_ANNOTATIONS, MODE_ROTATE_SCALE_BACKGROUND, ROLES } from '../../constants';

import hasCopyPasteFromAnotherPlan from '../../utils/has-copy-paste-from-another-plan';
import isScaling from '../../utils/is-scaling';
import PanelAutoLabellingFeedback from './panel-auto-labelling-feedback';
import PanelBackgroundImage from './panel-background-image';
import PanelContinuePipeline from './panel-continue-pipeline';
import PanelCopyPasteMode from './panel-copy-paste-mode';
import { PanelCreateAreaSplitters } from './panel-create-area-splitters';
import PanelElementEditor from './panel-element-editor/panel-element-editor';
import { PanelImportAnnotations } from './panel-import-annotations';
import PanelPlanDefaultHeights from './panel-plan-default-heights';
import PanelRotateScaleBackground from './panel-rotate-scale-background';
import PanelScale from './scale/panel-scale';
import PanelSiteStructure from './panel-site-structure';
import PanelValidationErrors from './panel-validation-errors';

const STYLE = {
  backgroundColor: SharedStyle.PRIMARY_COLOR.main,
  display: 'block',
  overflowY: 'auto',
  overflowX: 'hidden',
  paddingBottom: '20px',
};

// @TODO: Move this file to TS

const isSiteStructureLoaded = siteStructure => siteStructure && siteStructure.planId;
const isPlanInfoLoaded = state => state.planInfo?.id;
const hasScaleBeenValidated = state => state.scaleValidated;

const userRole = getUserRoles();
const isAdmin = userRole.includes(ROLES.ADMIN);

export default function Sidebar({ state, width, height, stateExtractor }) {
  const { selectedLayer } = state.scene;

  //TODO change in multi-layer check
  const selected = state.scene.layers[selectedLayer].selected;

  const multiselected =
    selected?.lines.length > 1 ||
    selected?.items.length > 1 ||
    selected?.holes.length > 1 ||
    selected?.areas.length > 1 ||
    selected?.lines.length + selected?.items.length + selected?.holes.length + selected?.areas.length > 1;

  const sorter = [
    { index: 1, name: 'PanelElementEditor', condition: !multiselected, dom: <PanelElementEditor state={state} /> },
    //{ index: 5, condition: multiselected, dom: <PanelMultiElementsEditor state={state} /> },
    {
      index: 2,
      name: 'PanelScale',
      condition: isScaling(state),
      dom: (
        <>
          <PanelScale stateExtractor={stateExtractor} />
        </>
      ),
    },
    {
      index: 3,
      name: 'PanelSiteStructure',
      condition: isSiteStructureLoaded(state.siteStructure),
      dom: <PanelSiteStructure siteStructure={state.siteStructure} />,
    },
    {
      index: 3,
      name: 'PanelPlanDefaultHeights',
      condition: isPlanInfoLoaded(state),
      dom: <PanelPlanDefaultHeights />,
    },
    {
      index: 3,
      name: 'PanelImportAnnotations',
      condition: isSiteStructureLoaded(state.siteStructure) && state.mode === MODE_IMPORT_ANNOTATIONS,
      dom: <PanelImportAnnotations />,
    },
    {
      index: 3,
      name: 'PanelContinuePipeline',
      condition: state.annotationFinished && !state.showBackgroundOnly,
      dom: <PanelContinuePipeline state={state} />,
    },
    {
      index: 4,
      name: 'PanelValidationErrors',
      condition: state.validationErrors.length > 0,
      dom: <PanelValidationErrors />,
    },
    {
      index: 5,
      name: 'PanelBackgroundImage',
      condition: state.showBackgroundOnly,
      dom: <PanelBackgroundImage />,
    },
    {
      index: 6,
      name: 'PanelAutoLabellingFeedback',
      condition: state.showAutoLabellingFeedback,
      dom: <PanelAutoLabellingFeedback />,
    },
    {
      index: 7,
      name: 'PanelRotateScaleBackground',
      condition: state.mode == MODE_ROTATE_SCALE_BACKGROUND,
      dom: <PanelRotateScaleBackground />,
    },
    {
      index: 8,
      name: 'PanelCopyPasteMode',
      condition:
        state.mode == MODE_COPY_PASTE ||
        (hasCopyPasteFromAnotherPlan(isPlanInfoLoaded(state)) && hasScaleBeenValidated(state)),
      dom: <PanelCopyPasteMode />,
    },
    {
      index: 9,
      name: 'PanelCreateAreaSplitters',
      condition: isSiteStructureLoaded(state.siteStructure) && isAdmin,
      dom: <PanelCreateAreaSplitters state={state} />,
    },
  ];

  const components = sorter
    .filter(({ condition }) => !!condition)
    .map(({ dom, name }) => {
      const elem = { ...dom, key: name };
      return elem;
    });

  return (
    <aside style={{ width, height, ...STYLE }} className="sidebar">
      {components}
    </aside>
  );
}

Sidebar.propTypes = {
  state: PropTypes.object.isRequired,
  width: PropTypes.number.isRequired,
  height: PropTypes.number.isRequired,
};
