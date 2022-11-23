import { FaExpand, FaMousePointer, FaPlus, FaRulerHorizontal } from 'react-icons/fa';
import { MdCopyAll, MdOutlineCropRotate, MdUndo } from 'react-icons/md';
import { BiImport, BiRectangle } from 'react-icons/bi';
import { bindActionCreators } from 'redux';
import { batch, connect } from 'react-redux';
import { IoMdHelp } from 'react-icons/io';
import React from 'react';
import { objectsMap } from '../../utils/objects-utils';
import { linesActions, projectActions } from '../../actions/export';
import {
  MODE_COPY_PASTE,
  MODE_HELP,
  MODE_IDLE,
  MODE_IMPORT_ANNOTATIONS,
  MODE_RECTANGLE_TOOL,
  MODE_ROTATE_SCALE_BACKGROUND,
  SCALING_REQUIRED_MEASUREMENT_COUNT,
  SNACKBAR_DURATION_FOREVER,
} from '../../constants';
import * as SharedStyle from '../../shared-style';
import ToolbarButton from '../toolbar-button/export';
import projectHasAnnotations from '../../utils/project-has-annotations';
import isScaling from '../../utils/is-scaling';
import ToolbarLogoutButton from './toolbar-logout-button';
import ToolbarSaveButton from './toolbar-save-button';

type ToolBarProps = {
  mode: string;
  alterate: boolean;
  scaleValidated: boolean;
  scaleAllowed: boolean;
  isScaling: boolean;
  mustImportAnnotations: boolean;
  catalogToolbarOpened: boolean;
  width: number;
  height: number;
  projectActions: any;
};

const ASIDE_STYLE = {
  backgroundColor: SharedStyle.PRIMARY_COLOR.main,
  padding: '10px',
  display: 'flex',
  flexDirection: 'column' as const,
};

const HR_STYLE = {
  width: '100%',
  marginBottom: '15px',
};

const Toolbar = React.memo(
  ({
    mode,
    alterate,
    scaleValidated,
    scaleAllowed,
    isScaling,
    mustImportAnnotations,
    catalogToolbarOpened,
    width,
    height,
    projectActions,
  }: ToolBarProps): JSX.Element => {
    const alterateColor = alterate ? SharedStyle.MATERIAL_COLORS[500].orange : '';

    const canDraw = scaleValidated && mode !== MODE_IMPORT_ANNOTATIONS;
    const sorter = [
      {
        condition: canDraw,
        dom: <ToolbarSaveButton />,
      },
      {
        condition: true,
        dom: (
          <ToolbarButton
            id="select-tool-button"
            active={[MODE_IDLE].includes(mode)}
            tooltip={'Select tool'}
            onClick={event => projectActions.setMode(MODE_IDLE)}
          >
            <FaMousePointer style={{ color: alterateColor }} />
          </ToolbarButton>
        ),
      },
      {
        condition: true,
        dom: (
          <ToolbarButton
            id="rectangle-select-tool-button"
            active={mode === MODE_RECTANGLE_TOOL}
            tooltip={'Rectangle select tool'}
            onClick={event => projectActions.setMode(MODE_RECTANGLE_TOOL)}
          >
            <BiRectangle style={{ color: alterateColor }} />
          </ToolbarButton>
        ),
      },
      {
        condition: true,
        dom: (
          <ToolbarButton active={false} tooltip={'Undo (CTRL-Z)'} onClick={event => projectActions.undo()}>
            <MdUndo />
          </ToolbarButton>
        ),
      },
      {
        condition: true,
        dom: (
          <ToolbarButton
            id="import-annotations-button"
            active={mode === MODE_IMPORT_ANNOTATIONS}
            tooltip={'Import annotations'}
            onClick={event => {
              mode === MODE_IMPORT_ANNOTATIONS
                ? projectActions.setMode(MODE_IDLE)
                : projectActions.setMode(MODE_IMPORT_ANNOTATIONS);
            }}
          >
            <BiImport />
          </ToolbarButton>
        ),
      },
      {
        condition: true,
        dom: (
          <ToolbarButton
            id="rotate-scale-background-button"
            active={mode === MODE_ROTATE_SCALE_BACKGROUND}
            tooltip={'Rotate/scale background'}
            onClick={event => {
              mode === MODE_ROTATE_SCALE_BACKGROUND
                ? projectActions.setMode(MODE_IDLE)
                : projectActions.setMode(MODE_ROTATE_SCALE_BACKGROUND);
            }}
          >
            <MdOutlineCropRotate />
          </ToolbarButton>
        ),
      },
      {
        condition: !mustImportAnnotations,
        dom: (
          <ToolbarButton
            active={isScaling}
            tooltip={'Scale tool'}
            onClick={event => {
              if (isScaling) {
                batch(() => {
                  projectActions.disableScaling();
                  projectActions.closeSnackbar();
                });
              } else {
                projectActions.enableScaling();
                if (scaleAllowed) {
                  projectActions.showSnackbar({
                    message: `Scale the plan by taking ${SCALING_REQUIRED_MEASUREMENT_COUNT} measures or setting page specs`,
                    severity: 'info',
                    duration: SNACKBAR_DURATION_FOREVER,
                  });
                }
              }
            }}
          >
            <FaRulerHorizontal />
          </ToolbarButton>
        ),
      },
      {
        condition: true,
        dom: (
          <ToolbarButton active={false} tooltip={'Fit to screen'} onClick={event => projectActions.fitToScreen()}>
            <FaExpand />
          </ToolbarButton>
        ),
      },
      {
        condition: canDraw,
        dom: (
          <ToolbarButton
            id="copy-paste-button"
            active={mode === MODE_COPY_PASTE}
            tooltip={'Copy & paste tool'}
            onClick={event => {
              mode === MODE_COPY_PASTE ? projectActions.setMode(MODE_IDLE) : projectActions.setMode(MODE_COPY_PASTE);
            }}
          >
            <MdCopyAll />
          </ToolbarButton>
        ),
      },
    ];

    const ToolbarButtons = sorter
      .filter(({ condition }) => !!condition)
      .map(({ dom }, idx) => {
        const elem = {
          ...dom,
          key: idx,
        };
        return elem;
      });

    return (
      <aside style={{ ...ASIDE_STYLE, maxWidth: width, maxHeight: height }} className="toolbar">
        {ToolbarButtons}
        {canDraw && (
          <>
            <hr style={HR_STYLE} />
            <ToolbarButton
              id="catalog-button"
              active={catalogToolbarOpened}
              tooltip={'Open catalog'}
              shortcut={'L'}
              onClick={() => projectActions.toggleCatalogToolbar()}
            >
              <FaPlus />
            </ToolbarButton>
          </>
        )}
        <ToolbarLogoutButton />
        <div style={{ marginTop: 'auto' }}>
          <ToolbarButton
            active={mode === MODE_HELP}
            tooltip={'Help'}
            onClick={event => {
              if (mode === MODE_HELP) {
                projectActions.setMode(MODE_IDLE);
              } else {
                projectActions.setMode(MODE_HELP);
              }
            }}
          >
            <IoMdHelp />
          </ToolbarButton>
        </div>
      </aside>
    );
  }
);

function mapStateToProps(state) {
  state = state['react-planner'];
  const { mode, alterate, scaleValidated, catalogToolbarOpened, mustImportAnnotations } = state;
  const scaleAllowed = !projectHasAnnotations(state);
  return {
    mode,
    isScaling: isScaling(state),
    alterate,
    scaleValidated,
    scaleAllowed,
    catalogToolbarOpened,
    mustImportAnnotations,
  };
}

const mapDispatchToProps = dispatch => {
  const actions = { projectActions, linesActions };
  const dispatchToProps = objectsMap(actions, actionNamespace =>
    bindActionCreators(actions[actionNamespace], dispatch)
  );
  return dispatchToProps;
};

export default connect(mapStateToProps, mapDispatchToProps)(Toolbar);
