import React from 'react';
import EntityView from 'Components/EntityView';
import formFields from 'Common/forms/building';
import { Building } from 'archilyse-ui-components';

const EditBuilding = ({ building, onEdit }: { building: Building; onEdit: () => void }): JSX.Element => (
  <EntityView fields={formFields} entity={building} context="building" onSubmit={onEdit} onSubmitDelete={onEdit} />
);

export default EditBuilding;
