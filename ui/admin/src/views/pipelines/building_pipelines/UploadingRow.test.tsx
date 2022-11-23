import * as React from 'react';
import { screen } from '@testing-library/react';
import { renderWithRouter } from '../../../../tests/utils';
import UploadingRow, { getUploadingFileName } from './UploadingRow';
import { UploadStatus as UPLOAD_STATUS } from './types';

const MOCK_UPLOADING_FLOOR = {
  data: {
    floorplan: ([{ name: 'sample_plan.pdf', item: '' }] as unknown) as FileList,
    floor_lower_range: '1',
    floor_upper_range: '1',
    building_id: 4481,
  },
};

describe('UploadingRow component', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    const route = '/pipelines?site_id=1455';
    return renderWithRouter(<UploadingRow {...props} />, route);
  };

  it('Shows a floor being uploaded', () => {
    const uploadingFloor = { ...MOCK_UPLOADING_FLOOR, status: UPLOAD_STATUS.IN_PROGRESS };
    renderComponent({ uploadingFloor });
    expect(
      screen.getByText(`Uploading ${getUploadingFileName(uploadingFloor.data)}`, { exact: false })
    ).toBeInTheDocument();
  });

  it('Shows when an upload of a floor failed', () => {
    const uploadingFloor = {
      ...MOCK_UPLOADING_FLOOR,
      status: UPLOAD_STATUS.FAILED,
      error: { response: { data: { msg: 'Castrophic failure' } } },
    };
    renderComponent({ uploadingFloor });
    const expectedText = screen.getByText(`Error uploading ${getUploadingFileName(uploadingFloor.data)}`, {
      exact: false,
    });

    expect(expectedText).toBeInTheDocument();
  });
});
