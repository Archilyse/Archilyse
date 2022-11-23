import * as React from 'react';
import { C } from 'Common';
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithRouter } from '../../../../tests/utils';
import PipelineRow from './PipelineRow';
import { UploadStatus as UPLOAD_STATUS, UploadingFloor } from './types';

const MOCK_SUCCESS_UPLOADING_FLOOR: UploadingFloor = {
  status: UPLOAD_STATUS.SUCCESS,
  data: {
    floorplan: ([{ name: 'sample_plan.pdf', item: '' }] as unknown) as FileList,
    floor_lower_range: '1',
    floor_upper_range: '1',
    building_id: 4481,
  },
};

const { PIPELINE } = C.URLS;

const PIPELINES_STEPS = [
  { name: 'labelled', url: PIPELINE.LABELLING },
  { name: 'classified', url: PIPELINE.CLASSIFICATION },
  { name: 'georeferenced', url: PIPELINE.GEOREFERENCE },
  { name: 'splitted', url: PIPELINE.SPLITTING },
  { name: 'units_linked', url: PIPELINE.LINKING },
];

const MOCK_PIPELINE = {
  building_housenumber: '1',
  building_id: 4481,
  classified: true,
  client_building_id: '10002',
  client_site_id: '10002',
  created: '2021-08-24T12:29:12.385337',
  floor_numbers: [1],
  georeferenced: true,
  id: 12648,
  is_masterplan: false,
  labelled: true,
  splitted: true,
  units_linked: true,
  updated: '2022-01-31T11:19:26.873901',
};

describe('PipelineRow component', () => {
  let props;
  const renderComponent = (changedProps = {}) => {
    props = { ...props, ...changedProps };
    const route = '/pipelines?site_id=1455';
    return renderWithRouter(<PipelineRow {...props} />, route);
  };

  beforeEach(() => {
    props = {
      pipeline: {},
      onClickEdit: () => {},
      onSelectMasterPlan: () => {},
      masterPlanId: undefined,
      uploadingFloor: undefined,
      masterPlanSelected: true,
    };
  });

  const CASE_1 = { ...MOCK_PIPELINE };
  const CASE_2 = { ...MOCK_PIPELINE, georeferenced: false, splitted: false };
  const CASE_3 = {
    ...MOCK_PIPELINE,
    labelled: false,
    classified: false,
    units_linked: false,
    georeferenced: false,
    splitted: false,
  };
  it.each([[CASE_1], [CASE_2], [CASE_3]])('Shows a step of the pipeline with its status and a link to it', pipeline => {
    renderComponent({ pipeline }); // @TODO
    PIPELINES_STEPS.forEach(step => {
      const stepCell = screen.getByTestId(`step-${step.name}`);

      const completedStep = pipeline[step.name];
      if (completedStep) {
        expect(within(stepCell).getByText('check')).toBeInTheDocument();
      } else {
        expect(within(stepCell).getByText('close')).toBeInTheDocument();
      }
      expect(within(stepCell).getByRole('link').getAttribute('href')).toBe(step.url(pipeline.id));
    });
  });

  it('Shows a successfully uploaded floor', () => {
    renderComponent({ pipeline: MOCK_PIPELINE, uploadingFloor: MOCK_SUCCESS_UPLOADING_FLOOR });
    const expectedText = `Floor ${MOCK_PIPELINE.floor_numbers
      .sort((a, b) => Number(a) - Number(b))
      .join(',')} uploaded successfully`;

    expect(screen.getByText(expectedText, { exact: false }));
  });

  it('Edit button is clickable', () => {
    const onClickEdit = jest.fn();
    renderComponent({ pipeline: MOCK_PIPELINE, onClickEdit });

    userEvent.click(screen.getByText('edit'));
    expect(onClickEdit).toHaveBeenCalled();
  });

  it('Select master plan radio button is clickable', () => {
    const onSelectMasterPlan = jest.fn();
    renderComponent({ pipeline: MOCK_PIPELINE, onSelectMasterPlan });

    userEvent.click(screen.getByRole('radio'));
    expect(onSelectMasterPlan).toHaveBeenCalled();
  });
});
