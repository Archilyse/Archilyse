import { OPENING_NAME } from '../../constants';
import React from 'react';
import { toFixedFloat } from '../../utils/math';
import { objectsMap } from '../../utils/objects-utils';
import * as projectActions from '../../actions/project-actions';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';

const m2cm = 100;

class OpeningHeightsInputForm extends React.Component {
  constructor(props) {
    super(props);
    let displayValues = this.getDisplayValues();

    this.state = {
      formValues: {
        lower_edge: displayValues.lower_edge,
        upper_edge: displayValues.upper_edge,
      },
    };
  }

  openingType() {
    return this.props.sourceElement.name;
  }

  planInfo() {
    let planInfo = this.props.state.planInfo;
    return planInfo;
  }

  currentValues() {
    let currentValues = this.props.value;
    return currentValues;
  }

  defaultHeights() {
    let openingType = this.openingType();
    let planInfo = this.planInfo();
    if ([OPENING_NAME.DOOR, OPENING_NAME.ENTRANCE_DOOR, OPENING_NAME.SLIDING_DOOR].includes(openingType)) {
      return [0, Math.floor(planInfo.default_door_height * m2cm)];
    }
    if (OPENING_NAME.WINDOW == openingType) {
      return [
        Math.floor(planInfo.default_window_lower_edge * m2cm),
        Math.floor(planInfo.default_window_upper_edge * m2cm),
      ];
    }
    return [null, null];
  }

  getDisplayValues() {
    // If the opening element has no heights, we display the plan default heights of the element type
    let openingType = this.openingType();
    let planInfo = this.planInfo();
    let currentValues = this.currentValues();
    const [defaultLowerEdge, defaultUpperEdge] = planInfo ? this.defaultHeights(planInfo, openingType) : [null, null];

    return {
      lower_edge: currentValues.lower_edge != null ? currentValues.lower_edge : defaultLowerEdge,
      upper_edge: currentValues.upper_edge != null ? currentValues.upper_edge : defaultUpperEdge,
    };
  }

  onSubmit = e => {
    e.preventDefault();
    const { projectActions } = this.props;
    let inputLowerEdge = toFixedFloat(this.state.formValues.lower_edge);
    let inputUpperEdge = toFixedFloat(this.state.formValues.upper_edge);
    const maxHeight = this.planInfo() ? this.planInfo().default_wall_height * m2cm : Infinity;
    if (inputLowerEdge > inputUpperEdge || inputLowerEdge < 0 || inputUpperEdge > maxHeight) {
      let message = '';
      if (inputLowerEdge > inputUpperEdge) {
        message = 'Upper edge must be bigger than smaller edge';
      } else {
        inputLowerEdge < 0
          ? (message = 'Lower edge can not be smaller than 0')
          : (message = 'Upper edge can not be bigger than wall height');
      }
      projectActions.showSnackbar({
        message: message,
        severity: 'error',
      });
      return this.setState({ formValues: this.getDisplayValues() });
    }

    this.props.onUpdate({ lower_edge: inputLowerEdge, upper_edge: inputUpperEdge });
    projectActions.showSnackbar({
      message: 'The opening heights have been set successfully',
      severity: 'success',
      duration: 2000,
    });
  };

  onChange = e => {
    const name = e.target.name;
    const value = e.target.value;
    let newFormValues = { lower_edge: this.state.formValues.lower_edge, upper_edge: this.state.formValues.upper_edge };
    newFormValues[name] = value;
    this.setState({ formValues: newFormValues });
  };

  render() {
    return (
      <form onSubmit={this.onSubmit}>
        <table className="OpeningHeightsInputForm">
          <tbody>
            <tr>
              <th colSpan={2} style={{ whiteSpace: 'nowrap' }}>
                Selected Opening Heights
              </th>
            </tr>
            <tr>
              <td style={{ whiteSpace: 'nowrap' }}>Lower [cm]</td>
              <td>
                <input
                  name="lower_edge"
                  type="number"
                  value={this.state.formValues.lower_edge}
                  onChange={this.onChange}
                />
              </td>
            </tr>
            <tr>
              <td style={{ whiteSpace: 'nowrap' }}>Upper [cm]</td>
              <td>
                <input
                  name="upper_edge"
                  type="number"
                  value={this.state.formValues.upper_edge}
                  onChange={this.onChange}
                />
              </td>
            </tr>
            <tr>
              <th colSpan={2}>
                <button className="btn btn-primary" id="save-heights-button" type="submit">
                  Save heights
                </button>
              </th>
            </tr>
          </tbody>
        </table>
      </form>
    );
  }
}

const mapDispatchToProps = dispatch => {
  const actions = { projectActions };
  const dispatchToProps = objectsMap(actions, actionNamespace =>
    bindActionCreators(actions[actionNamespace], dispatch)
  );
  return dispatchToProps;
};

export default connect(null, mapDispatchToProps)(OpeningHeightsInputForm);
