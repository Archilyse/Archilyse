import cn from 'classnames';
import React from 'react';
import { Icon } from 'archilyse-ui-components';
import { Pipeline as PipelineType } from 'Common/types';
import './buildingPipelines.scss';
import { C } from 'Common';
import { Tooltip } from '@material-ui/core';
import { Link } from 'react-router-dom';
import { UploadStatus as UPLOAD_STATUS, UploadingFloor } from './types';

const { PIPELINE } = C.URLS;
const LINK_COLOR = '#0000ee';

const PipelineStep = ({ step, url, showLink }: { step: boolean; url; showLink }) => {
  return (
    <div className="status">
      <div style={{ color: step ? 'green' : 'red' }}>
        <Icon style={{ color: 'inherit', marginLeft: undefined }}>{step ? 'check' : 'close'}</Icon>
      </div>
      {showLink && (
        <a href={url} target="_blank" rel="noreferrer">
          <Icon style={{ color: LINK_COLOR, fontSize: '14px' }}>launch</Icon>
        </a>
      )}
    </div>
  );
};

const isUploadedSuccessfully = (uploadingFloor, pipeline) => {
  const uploadIncludesNumber =
    pipeline.floor_numbers.includes(Number(uploadingFloor?.data.floor_lower_range)) ||
    pipeline.floor_numbers.includes(Number(uploadingFloor?.data.floor_upper_range));
  const isUploadedSuccessfully = uploadingFloor?.status === UPLOAD_STATUS.SUCCESS && uploadIncludesNumber;
  return isUploadedSuccessfully;
};

const PipelineRow = ({
  pipeline,
  onClickEdit,
  onSelectMasterPlan,
  masterPlanSelected,
  masterPlanId = undefined,
  uploadingFloor = undefined,
}: {
  masterPlanSelected: boolean;
  masterPlanId: number;
  pipeline: PipelineType;
  onSelectMasterPlan: () => void;
  onClickEdit: () => void;
  uploadingFloor?: UploadingFloor;
}): JSX.Element => {
  const pipelineHasBeenUpladed = isUploadedSuccessfully(uploadingFloor, pipeline);
  return (
    <tr
      className={cn({
        [UPLOAD_STATUS.SUCCESS]: pipelineHasBeenUpladed,
        'masterplan-row': pipeline.id === masterPlanId,
      })}
    >
      <td>
        Floor {pipeline.floor_numbers.sort((a, b) => Number(a) - Number(b)).join(',')}
        {pipelineHasBeenUpladed ? ' uploaded successfully' : ''}
      </td>
      <td className="plan-link">
        <Link to={C.URLS.PLAN(pipeline.id)} target="_blank" rel="noreferrer">
          Plan {pipeline.id}
        </Link>
      </td>
      <td data-testid="step-labelled">
        <PipelineStep step={pipeline.labelled} url={PIPELINE.LABELLING(pipeline.id)} showLink={masterPlanSelected} />
      </td>
      <td data-testid="step-classified">
        <PipelineStep
          step={pipeline.classified}
          url={PIPELINE.CLASSIFICATION(pipeline.id)}
          showLink={masterPlanSelected}
        />
      </td>
      <td data-testid="step-georeferenced">
        <PipelineStep
          step={pipeline.georeferenced}
          url={PIPELINE.GEOREFERENCE(pipeline.id)}
          showLink={masterPlanSelected}
        />
      </td>
      <td data-testid="step-splitted">
        <PipelineStep step={pipeline.splitted} url={PIPELINE.SPLITTING(pipeline.id)} showLink={masterPlanSelected} />
      </td>
      <td data-testid="step-units_linked">
        <PipelineStep step={pipeline.units_linked} url={PIPELINE.LINKING(pipeline.id)} showLink={masterPlanSelected} />
      </td>
      <td>
        <input
          type="radio"
          name={`masterplan-${pipeline.building_id}`}
          checked={pipeline.id === masterPlanId}
          onClick={onSelectMasterPlan}
        />
      </td>
      <td>
        {masterPlanSelected ? (
          <a href={PIPELINE.LABELLING(pipeline.id)} target="_blank" rel="noreferrer">
            Go to pipeline
          </a>
        ) : (
          <Tooltip title={'Select a master plan in the building before start labelling'}>
            <div>Go to pipeline</div>
          </Tooltip>
        )}
      </td>
      {/* Classname used in e2e tests */}
      <td className="edit-floor-button" onClick={onClickEdit}>
        <Icon style={{ fontSize: '20px' }}>edit</Icon>
      </td>
    </tr>
  );
};

export default PipelineRow;
