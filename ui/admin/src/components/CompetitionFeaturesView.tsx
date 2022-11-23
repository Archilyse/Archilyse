import React, { useContext } from 'react';
import { Form, SnackbarContext } from 'archilyse-ui-components';
import { ProviderRequest } from '../providers';

const CompetitionFeaturesView = ({ entity, context, fields, value }) => {
  const snackbar = useContext(SnackbarContext);

  const onSaveFeatures = async data => {
    const features = Object.keys(data).filter(key => data[key]);
    await ProviderRequest.put(`${context}/${entity.id}`, { features_selected: features });
    snackbar.show({ message: 'Saved successfully', severity: 'success' });
  };

  return (
    <>
      <div className="title competition-feature-title">
        <h2>Features Selection for competition {entity.name}</h2>
      </div>
      <br></br>
      <div>
        <Form id="CompetitionFeaturesForm" fields={fields} value={value} submitText="SAVE" onSubmit={onSaveFeatures} />
      </div>
    </>
  );
};

export default CompetitionFeaturesView;
