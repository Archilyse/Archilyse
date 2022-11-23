import React from 'react';
import EntityView from 'Components/EntityView';
import formFields from 'Common/forms/pipeline';
import { Pipeline } from 'Common/types';

const EditPipeline = ({ pipeline, onEdit }: { pipeline: Pipeline; onEdit: () => void }): JSX.Element => {
  const floor_numbers = pipeline.floor_numbers.sort();

  const formValues = {
    id: pipeline.id,
    name: 'Edit floor range/Delete Plan',
    floor_lower_range: floor_numbers.slice(0)[0],
    floor_upper_range: floor_numbers.slice(-1)[0],
  };
  return (
    <EntityView fields={formFields} entity={formValues} context="plan" onSubmit={onEdit} onSubmitDelete={onEdit} />
  );
};

export default EditPipeline;
