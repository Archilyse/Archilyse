import React from 'react';
import { Building } from 'archilyse-ui-components';
import { EntityView } from 'Components';
import formFields from 'Common/forms/floors';

const NewPipeline = ({ building, onClickCreate }: { building: Building; onClickCreate }) => {
  return (
    <EntityView
      fields={formFields.NEW}
      entity={{}}
      context="floor"
      parent={building}
      parentKey={'building_id'}
      onCreate={onClickCreate}
    />
  );
};

export default NewPipeline;
