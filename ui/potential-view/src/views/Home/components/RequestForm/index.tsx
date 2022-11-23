import React from 'react';
import { Icon, LoadingIndicator, RequestStateType, RequestStatus } from 'archilyse-ui-components';
import './requestForm.scss';

const LATITUDE_VALID_RANGE = { min: -90, max: 90 };
const LONGITUDE_VALID_RANGE = { min: -180, max: 180 };

const LOADING_STYLE = { width: 20, height: 20, color: 'white' };

export type RequestFormFields = {
  latitude: number;
  longitude: number;
  floor: number;
  simType: 'sun' | 'view';
};

type Props = {
  fields: RequestFormFields;
  onChange: (fields: RequestFormFields) => void;
  onSubmit: (simType: string, json) => void;
  requestState: RequestStateType;
};

const serialize = (fields: RequestFormFields) => ({
  lat: Number(fields.latitude),
  lon: Number(fields.longitude),
  floor_number: Number(fields.floor),
});

const RequestForm = ({ fields, onChange, onSubmit, requestState }: Props): JSX.Element => {
  const handleChange = (key: keyof typeof fields) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    onChange({ ...fields, [key]: event.target.value });
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();

    const json = serialize(fields);

    onSubmit(fields.simType, json);
  };

  const isLoading = requestState.status === RequestStatus.PENDING;
  const isRejected = requestState.status === RequestStatus.REJECTED && requestState.error;

  return (
    <form className="request-simulation-form" onSubmit={handleSubmit}>
      <div className="form-row">
        <label className="form-label">
          Latitude:
          <input
            name="latitude"
            type="number"
            className="potential-view-input"
            placeholder={`${LATITUDE_VALID_RANGE.min}...${LATITUDE_VALID_RANGE.max}`}
            value={fields.latitude || ''}
            onChange={handleChange('latitude')}
            required
            step="any"
            {...LATITUDE_VALID_RANGE}
          />
        </label>
        <label className="form-label">
          Longitude:
          <input
            name="longitude"
            type="number"
            className="potential-view-input"
            placeholder={`${LONGITUDE_VALID_RANGE.min}...${LONGITUDE_VALID_RANGE.max}`}
            value={fields.longitude || ''}
            onChange={handleChange('longitude')}
            required
            step="any"
            {...LONGITUDE_VALID_RANGE}
          />
        </label>
      </div>
      <div className="form-row">
        <label className="form-label">
          Floor number:
          <input
            name="floor"
            type="number"
            className="potential-view-input"
            value={fields.floor || ''}
            onChange={handleChange('floor')}
            required
          />
        </label>
        <label className="form-label">
          Simulation type:
          <select
            name="simType"
            className="potential-view-input"
            value={fields.simType}
            onChange={handleChange('simType')}
          >
            <option value="sun">Sun simulation</option>
            <option value="view">View simulation</option>
          </select>
        </label>
      </div>

      <div className="footer-row">
        <button type="submit" className="potential-view-button" disabled={isLoading}>
          Request simulation{isLoading && <LoadingIndicator style={LOADING_STYLE} />}
        </button>
      </div>

      {isRejected && (
        <div className="error-message">
          <Icon>error_outline</Icon>
          <p>{requestState.error}</p>
        </div>
      )}
    </form>
  );
};

export default RequestForm;
