import React from 'react';
import { UploadStatus as UPLOAD_STATUS, UploadingFloor } from './types/';
import { getErrorMessage, getUploadingFloorNumber } from './utils';

export const getUploadingFileName = (data: UploadingFloor['data']) => data.floorplan[0]?.name || '';

const UploadingRow = ({ uploadingFloor }: { uploadingFloor: UploadingFloor }) => {
  const { data, status, error } = uploadingFloor;
  const { IN_PROGRESS, FAILED } = UPLOAD_STATUS;

  return (
    <tr className={status}>
      <td>Floor {getUploadingFloorNumber(data)}</td>
      {status === IN_PROGRESS && (
        <td colSpan={9} className={`plan-link ${IN_PROGRESS}`}>
          Uploading {getUploadingFileName(data)}...
        </td>
      )}
      {status === FAILED && (
        <td colSpan={9}>
          Error uploading {getUploadingFileName(data)}: {getErrorMessage(error)}
        </td>
      )}
    </tr>
  );
};

export default UploadingRow;
