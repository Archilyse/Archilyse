import React, { useRef } from 'react';
import { batch, connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { FormNumberInput } from '../style/export';
import { ENDPOINTS } from '../../constants';
import { ProviderRequest } from '../../providers';
import { projectActions } from '../../actions/export';
import { objectsMap } from '../../utils/objects-utils';
import { usePlanId } from '../../hooks/export';
import Panel from './panel';

const UL_STYLE = { listStyleType: 'none', paddingRight: '20px', paddingLeft: '20px' };
const LI_STYLE = { display: 'flex', justifyContent: 'space-between', marginBottom: '5px' };
const LABEL_STYLE = { width: '80%', paddingRight: '2px' };

const PanelPlanDefaultHeightsProps = ({
  default_wall_height,
  default_door_height,
  default_window_lower_edge,
  default_window_upper_edge,
  default_ceiling_slab_height,
  projectActions,
}: any) => {
  const partialPlanInfo = {
    default_wall_height,
    default_door_height,
    default_window_lower_edge,
    default_window_upper_edge,
    default_ceiling_slab_height,
  };
  const partialPlanInfoRef = useRef(partialPlanInfo);
  const planId = usePlanId();

  async function saveHeights() {
    try {
      await ProviderRequest.patch(ENDPOINTS.PLAN_HEIGHTS(planId), {
        default_wall_height: partialPlanInfoRef.current.default_wall_height,
        default_door_height: partialPlanInfoRef.current.default_door_height,
        default_window_lower_edge: partialPlanInfoRef.current.default_window_lower_edge,
        default_window_upper_edge: partialPlanInfoRef.current.default_window_upper_edge,
        default_ceiling_slab_height: partialPlanInfoRef.current.default_ceiling_slab_height,
      });

      batch(() => {
        projectActions.setPlanInfo(partialPlanInfoRef.current);
        projectActions.showSnackbar({
          message: 'The default plan heights have been set successfully',
          severity: 'success',
          duration: 2000,
        });
      });
    } catch (error) {
      projectActions.showSnackbar({
        message:
          'An error occured setting the default plan heights, please note: door < wall, lower_window_edge < upper_window_edge < wall_height',
        severity: 'error',
      });
    }
  }

  return (
    <Panel name={`Plan ${planId} - Default heights`} opened={false}>
      <ul style={UL_STYLE}>
        <li style={LI_STYLE}>
          <label style={LABEL_STYLE}>Wall Height [cm]:</label>
          <div>
            <FormNumberInput
              value={default_wall_height * 100}
              onChange={e => {
                const changedValue = parseFloat(e.target.value) / 100;
                partialPlanInfoRef.current.default_wall_height = changedValue;
              }}
            />
          </div>
        </li>
        <li style={LI_STYLE}>
          <label style={LABEL_STYLE}>Door Height [cm]:</label>
          <div>
            <FormNumberInput
              value={default_door_height * 100}
              onChange={e => {
                const changedValue = parseFloat(e.target.value) / 100;
                partialPlanInfoRef.current.default_door_height = changedValue;
              }}
            />
          </div>
        </li>
        <li style={LI_STYLE}>
          <label style={LABEL_STYLE}>Window Lower Edge [cm]:</label>
          <div>
            <FormNumberInput
              value={default_window_lower_edge * 100}
              onChange={e => {
                const changedValue = parseFloat(e.target.value) / 100;
                partialPlanInfoRef.current.default_window_lower_edge = changedValue;
              }}
            />
          </div>
        </li>
        <li style={LI_STYLE}>
          <label style={LABEL_STYLE}>Window Upper Edge [cm]:</label>
          <div>
            <FormNumberInput
              value={default_window_upper_edge * 100}
              onChange={e => {
                const changedValue = parseFloat(e.target.value) / 100;
                partialPlanInfoRef.current.default_window_upper_edge = changedValue;
              }}
            />
          </div>
        </li>
        <li style={LI_STYLE}>
          <label style={LABEL_STYLE}>Floor Slab Height [cm]:</label>
          <div>
            <FormNumberInput
              value={default_ceiling_slab_height * 100}
              onChange={e => {
                const changedValue = parseFloat(e.target.value) / 100;
                partialPlanInfoRef.current.default_ceiling_slab_height = changedValue;
              }}
            />
          </div>
        </li>
        <li>
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              flexDirection: 'column',
              padding: '10px',
            }}
          >
            <button className="primary-button" onClick={saveHeights}>
              Save Default heights
            </button>
          </div>
        </li>
      </ul>
    </Panel>
  );
};

function mapStateToProps(state) {
  state = state['react-planner'];
  const { planInfo } = state;
  const {
    default_wall_height,
    default_door_height,
    default_window_lower_edge,
    default_window_upper_edge,
    default_ceiling_slab_height,
  } = planInfo;
  return {
    default_wall_height,
    default_door_height,
    default_window_lower_edge,
    default_window_upper_edge,
    default_ceiling_slab_height,
  };
}

const mapDispatchToProps = dispatch => {
  const actions = { projectActions };
  const dispatchToProps = objectsMap(actions, actionNamespace =>
    bindActionCreators(actions[actionNamespace], dispatch)
  );
  return dispatchToProps;
};

export default connect(mapStateToProps, mapDispatchToProps)(PanelPlanDefaultHeightsProps);
