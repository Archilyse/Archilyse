import React, { useContext, useEffect, useState } from 'react';
import { Building, Icon, SnackbarContext } from 'archilyse-ui-components';
import { Pipeline as PipelineType } from 'Common/types';
import './buildingPipelines.scss';
import { Modal } from '@material-ui/core';
import { C } from 'Common';
import { ProviderRequest } from 'Providers';
import NewPipeline from './NewPipeline';
import EditPipeline from './EditPipeline';
import PipelineRow from './PipelineRow';
import { UploadStatus as UPLOAD_STATUS, UploadingFloor } from './types/';
import { findBiggerPlans, getErrorMessage, getUploadingFloorNumber } from './utils/';
import UploadingRow from './UploadingRow';

const BuildingPipelines = ({
  pipelines,
  building,
  enforceMasterplan,
  onFloorUpload,
  reloadPipelines,
}: {
  pipelines: PipelineType[];
  enforceMasterplan: boolean;
  building: Building;
  onFloorUpload: ({ failed: boolean }) => void;
  reloadPipelines: () => void;
}): JSX.Element => {
  const [openAddModal, setOpenAddModal] = useState(false);
  const [pipelineToEdit, setPipelineToEdit] = useState<PipelineType>(undefined);
  const [uploadingFloor, setUploadingFloor] = useState<UploadingFloor>(undefined);
  const [masterPlanId, setMasterPlanId] = useState<number>(undefined);

  const snackbar = useContext(SnackbarContext);

  const onClickCreatePipeline = async data => {
    data.building_id = building.id;
    setOpenAddModal(false);
    setUploadingFloor({ status: UPLOAD_STATUS.IN_PROGRESS, data });
    try {
      snackbar.show({ message: `Uploading floor ${getUploadingFloorNumber(data)}...`, severity: 'info' });
      await ProviderRequest.multipart(C.ENDPOINTS.FLOOR(), data);
      setUploadingFloor({ status: UPLOAD_STATUS.SUCCESS, data });
      snackbar.show({ message: `Floor ${getUploadingFloorNumber(data)} upload successfully`, severity: 'success' });
      reloadPipelines();
      onFloorUpload({ failed: false });
    } catch (error) {
      snackbar.show({
        message: `Error uploading floor ${getUploadingFloorNumber(data)}: ${getErrorMessage(error)}`,
        severity: 'error',
      });
      setUploadingFloor({ status: UPLOAD_STATUS.FAILED, data, error: error });
      onFloorUpload({ failed: true });
    }
  };

  useEffect(() => {
    if (!masterPlanId) {
      const masterPlan = pipelines.find(p => p.is_masterplan);
      setMasterPlanId(masterPlan?.id);
    }
  }, [pipelines, masterPlanId]);

  const onSelectMasterPlan = async (planId: number) => {
    setMasterPlanId(planId);

    await ProviderRequest.put(C.ENDPOINTS.SET_MASTERPLAN(planId), {});
    const currentMasterPlan = { id: planId, building_id: building.id };
    const biggerPlans = await findBiggerPlans(pipelines, currentMasterPlan);

    if (biggerPlans.length > 0) {
      snackbar.show({
        message: `The selected master plan is smaller than the plans: {${biggerPlans.join(
          ','
        )}}, this may affect the labelling`,
        severity: 'warning',
      });
    }
    reloadPipelines();
  };
  const onEditPipeline = () => {
    setPipelineToEdit(undefined);
    reloadPipelines();
  };

  const showUploadingRow =
    uploadingFloor?.status === UPLOAD_STATUS.FAILED || uploadingFloor?.status === UPLOAD_STATUS.IN_PROGRESS;

  return (
    <>
      <table className="building-pipelines">
        <thead className="building-pipelines-header">
          <th></th> {/* Floor numbers */}
          <th></th> {/* Plan link */}
          <th>Labelled</th>
          <th>Classified</th>
          <th>Georeferenced</th>
          <th>Splitted</th>
          <th>Units linked</th>
          <th>Masterplan</th>
          <th></th> {/* Go to pipeline link */}
          <th></th> {/* Edit button */}
        </thead>
        <tbody>
          {pipelines
            .sort((a, b) =>
              Number(
                a.floor_numbers.sort((a, b) => Number(a - b))[0] - b.floor_numbers.sort((a, b) => Number(a - b))[0]
              )
            )
            .map(pipeline => (
              <PipelineRow
                masterPlanSelected={enforceMasterplan ? Boolean(masterPlanId) : true}
                key={pipeline.id}
                pipeline={pipeline}
                masterPlanId={masterPlanId}
                onSelectMasterPlan={() => onSelectMasterPlan(pipeline.id)}
                onClickEdit={() => setPipelineToEdit(pipeline)}
                uploadingFloor={uploadingFloor}
              />
            ))}
          {showUploadingRow && <UploadingRow uploadingFloor={uploadingFloor} />}
          <tr>
            <td className="add-button" onClick={() => setOpenAddModal(true)}>
              <Icon style={{ marginRight: '5px', color: 'inherit', fontSize: '20px' }}>add_circle</Icon>
              <p>Add...</p>
            </td>
          </tr>
        </tbody>
      </table>
      <Modal open={openAddModal} onClose={() => setOpenAddModal(false)} style={C.CSS.MODAL_STYLE}>
        <div className="crud-modal">
          <NewPipeline building={building} onClickCreate={onClickCreatePipeline} />
        </div>
      </Modal>
      <Modal open={Boolean(pipelineToEdit)} onClose={() => setPipelineToEdit(undefined)} style={C.CSS.MODAL_STYLE}>
        <div className="crud-modal">
          <EditPipeline pipeline={pipelineToEdit} onEdit={onEditPipeline} />
        </div>
      </Modal>
    </>
  );
};

export default BuildingPipelines;
