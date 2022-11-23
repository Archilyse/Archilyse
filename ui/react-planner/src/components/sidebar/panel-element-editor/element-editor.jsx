import React, { Component } from 'react';
import PropTypes from 'prop-types';
import convert from 'convert-units';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import { GeometryUtils, MathUtils } from '../../../utils/export';
import { MODE_DRAWING_LINE } from '../../../constants';
import { ProviderHash } from '../../../providers';
import { objectsMap } from '../../../utils/objects-utils';
import { planActions, projectActions } from '../../../actions/export';
import MyCatalog from '../../../catalog-elements/mycatalog';

const PRECISION = 2;

class ElementEditor extends Component {
  constructor(props, context) {
    super(props, context);

    this.state = {
      attributesFormData: this.initAttrData(this.props.element, this.props.layer, this.props.state),
      propertiesFormData: this.initPropData(this.props.element, this.props.layer, this.props.state),
    };

    this.updateAttribute = this.updateAttribute.bind(this);
  }

  componentWillReceiveProps({ element, layer, state }) {
    const widthHasChanged =
      element.properties.width?.value !== this.state.propertiesFormData?.width?.currentValue.value;
    const lengthHasChanged =
      element.properties.length?.value !== this.state.propertiesFormData.length?.currentValue.value;
    const referenceLineHasChanged =
      element.properties.referenceLine !== this.state.propertiesFormData.referenceLine?.currentValue;

    if (widthHasChanged || lengthHasChanged || referenceLineHasChanged)
      this.setState({
        attributesFormData: this.initAttrData(element, layer, state),
        propertiesFormData: this.initPropData(element, layer, state),
      });
  }

  initAttrData(element, layer, state) {
    element = typeof element.misc === 'object' ? element.set('misc', element.misc) : element;

    switch (element.prototype) {
      case 'items': {
        return {};
      }
      case 'lines': {
        return {};
      }
      case 'holes': {
        return {};
      }
      case 'areas': {
        return {};
      }
      default:
        return null;
    }
  }

  initActionsData(element) {
    const catalog = MyCatalog;
    const catalogElement = catalog.getElement(element.type);
    const mapped = {};
    for (const action in catalogElement.actions) {
      mapped[action] = {
        onClick: catalogElement.actions[action].onClick,
        text: catalogElement.actions[action].text,
      };
    }
    return mapped;
  }

  initPropData(element, layer, state) {
    const catalog = MyCatalog;
    const catalogElement = catalog.getElement(element.type);

    const mapped = {};
    for (const name in catalogElement.properties) {
      mapped[name] = {
        currentValue: element.properties[name]
          ? element.properties[name]
          : catalogElement.properties[name].defaultValue,
        configs: catalogElement.properties[name],
      };
    }

    return mapped;
  }

  // @TODO: Erase all non used code here
  updateAttribute(attributeName, value) {
    let { attributesFormData } = this.state;
    const catalog = MyCatalog;
    switch (this.props.element.prototype) {
      case 'items': {
        attributesFormData = attributesFormData.set(attributeName, value);
        break;
      }
      case 'lines': {
        switch (attributeName) {
          case 'lineLength': {
            const v_0 = attributesFormData.get('vertexOne');
            const v_1 = attributesFormData.get('vertexTwo');

            const [v_a, v_b] = GeometryUtils.orderVertices([v_0, v_1]);

            const v_b_new = GeometryUtils.extendLine(v_a.x, v_a.y, v_b.x, v_b.y, value.get('value'), PRECISION);

            attributesFormData = attributesFormData.withMutations(attr => {
              attr.set(v_0 === v_a ? 'vertexTwo' : 'vertexOne', v_b.merge(v_b_new));
              attr.set('lineLength', value);
            });
            break;
          }
          default: {
            attributesFormData = attributesFormData.set(attributeName, value);
            break;
          }
        }
        break;
      }
      case 'holes': {
        switch (attributeName) {
          case 'offsetA': {
            const line = this.props.layer.lines.get(this.props.element.line);

            const orderedVertices = GeometryUtils.orderVertices([
              this.props.layer.vertices.get(line.vertices.get(0)),
              this.props.layer.vertices.get(line.vertices.get(1)),
            ]);

            const [{ x: x0, y: y0 }, { x: x1, y: y1 }] = orderedVertices;

            const alpha = GeometryUtils.angleBetweenTwoPoints(x0, y0, x1, y1);
            const lineLength = GeometryUtils.pointsDistance(x0, y0, x1, y1);
            const holeLength = this.props.element.properties.get('length').get('value');
            const halfHoleLength = holeLength / 2;

            let lengthValue = value.get('value');
            lengthValue = Math.max(lengthValue, 0);
            lengthValue = Math.min(lengthValue, lineLength - holeLength);

            const xp = (lengthValue + halfHoleLength) * Math.cos(alpha) + x0;
            const yp = (lengthValue + halfHoleLength) * Math.sin(alpha) + y0;

            const offset = GeometryUtils.pointPositionOnLineSegment(x0, y0, x1, y1, xp, yp);

            const endAt = MathUtils.toFixedFloat(lineLength - lineLength * offset - halfHoleLength, PRECISION);
            const offsetUnit = attributesFormData.getIn(['offsetB', '_unit']);

            const offsetB = {
              length: endAt,
              _length: convert(endAt).from(catalog.unit).to(offsetUnit),
              _unit: offsetUnit,
            };

            attributesFormData = attributesFormData.set('offsetB', offsetB).set('offset', offset);

            const offsetAttribute = {
              length: MathUtils.toFixedFloat(lengthValue, PRECISION),
              _unit: value.get('_unit'),
              _length: MathUtils.toFixedFloat(
                convert(lengthValue).from(catalog.unit).to(value.get('_unit')),
                PRECISION
              ),
            };

            attributesFormData = attributesFormData.set(attributeName, offsetAttribute);

            break;
          }
          case 'offsetB': {
            const line = this.props.layer.lines.get(this.props.element.line);

            const orderedVertices = GeometryUtils.orderVertices([
              this.props.layer.vertices.get(line.vertices.get(0)),
              this.props.layer.vertices.get(line.vertices.get(1)),
            ]);

            const [{ x: x0, y: y0 }, { x: x1, y: y1 }] = orderedVertices;

            const alpha = GeometryUtils.angleBetweenTwoPoints(x0, y0, x1, y1);
            const lineLength = GeometryUtils.pointsDistance(x0, y0, x1, y1);
            const holeLength = this.props.element.properties.get('length').get('value');
            const halfHoleLength = holeLength / 2;

            let lengthValue = value.get('value');
            lengthValue = Math.max(lengthValue, 0);
            lengthValue = Math.min(lengthValue, lineLength - holeLength);

            const xp = x1 - (lengthValue + halfHoleLength) * Math.cos(alpha);
            const yp = y1 - (lengthValue + halfHoleLength) * Math.sin(alpha);

            const offset = GeometryUtils.pointPositionOnLineSegment(x0, y0, x1, y1, xp, yp);

            const startAt = MathUtils.toFixedFloat(lineLength * offset - halfHoleLength, PRECISION);
            const offsetUnit = attributesFormData.getIn(['offsetA', '_unit']);

            const offsetA = {
              length: startAt,
              _length: convert(startAt).from(catalog.unit).to(offsetUnit),
              _unit: offsetUnit,
            };

            attributesFormData = attributesFormData.set('offsetA', offsetA).set('offset', offset);

            const offsetAttribute = {
              length: MathUtils.toFixedFloat(lengthValue, PRECISION),
              _unit: value.get('_unit'),
              _length: MathUtils.toFixedFloat(
                convert(lengthValue).from(catalog.unit).to(value.get('_unit')),
                PRECISION
              ),
            };

            attributesFormData = attributesFormData.set(attributeName, offsetAttribute);

            break;
          }
          default: {
            attributesFormData = attributesFormData.set(attributeName, value);
            break;
          }
        }
        break;
      }
      default:
        break;
    }

    this.setState({ attributesFormData });
    this.save({ attributesFormData });
  }

  updateProperty(propertyName, value) {
    let {
      state: { propertiesFormData },
    } = this;
    propertiesFormData = {
      ...propertiesFormData,
      [propertyName]: {
        ...propertiesFormData[propertyName],
        currentValue: value,
      },
    };
    this.save({ propertiesFormData });
  }

  reset() {
    this.setState({ propertiesFormData: this.initPropData(this.props.element, this.props.layer, this.props.state) });
  }

  save({ propertiesFormData, attributesFormData }) {
    const { projectActions } = this.props;
    if (propertiesFormData) {
      const properties = Object.entries(propertiesFormData).reduce((acc, [key, data]) => {
        const { currentValue } = data;
        acc[key] = currentValue;
        return acc;
      }, {});
      projectActions.setProperties(properties);
    }

    if (attributesFormData) {
      switch (this.props.element.prototype) {
        case 'items': {
          projectActions.setItemsAttributes(attributesFormData);
          break;
        }
        case 'lines': {
          projectActions.setLinesAttributes(attributesFormData);
          break;
        }
        case 'holes': {
          projectActions.setHolesAttributes(attributesFormData);
          break;
        }
      }
    }
  }

  copyProperties(properties) {
    this.props.projectActions.copyProperties(properties);
  }

  pasteProperties() {
    this.props.projectActions.pasteProperties();
  }

  render() {
    const {
      state: { propertiesFormData, attributesFormData },
      props: { state: appState, element },
    } = this;

    const catalogElement = MyCatalog.getElement(element.type);

    return (
      <div style={{ marginBottom: '5px' }}>
        {Object.entries(propertiesFormData).map(([propertyName, data]) => {
          const currentValue = data.currentValue;
          const configs = Object.assign({}, data.configs);

          switch (propertyName) {
            case 'areaType':
              configs.values = appState.availableAreaTypes;
              break;
            case 'referenceLine':
              /**
               * If the `type` is "hidden" that means that the element is an area splitter
               */
              if (configs.type !== 'hidden') {
                configs.type = appState.mode !== MODE_DRAWING_LINE ? 'read-only' : configs.type;
              }
              break;
          }

          const { Editor } = MyCatalog.getPropertyType(configs.type);
          return (
            <Editor
              key={propertyName}
              propertyName={propertyName}
              value={currentValue}
              configs={configs}
              onUpdate={value => this.updateProperty(propertyName, value)}
              state={appState}
              sourceElement={element}
              internalState={this.state}
            />
          );
        })}
        {catalogElement.help && (
          <>
            {catalogElement.help.split('\n').map(text => (
              <>
                <br />
                <label>{text}</label>
                <br />
              </>
            ))}
          </>
        )}
      </div>
    );
  }
}

ElementEditor.propTypes = {
  state: PropTypes.object.isRequired,
  element: PropTypes.object.isRequired,
  layer: PropTypes.object.isRequired,
};

function mapStateToProps(state) {
  state = state['react-planner'];
  return {
    state,
  };
}

const mapDispatchToProps = dispatch => {
  const actions = { planActions, projectActions };
  const dispatchToProps = objectsMap(actions, actionNamespace =>
    bindActionCreators(actions[actionNamespace], dispatch)
  );
  return dispatchToProps;
};

export default connect(mapStateToProps, mapDispatchToProps)(ElementEditor);
