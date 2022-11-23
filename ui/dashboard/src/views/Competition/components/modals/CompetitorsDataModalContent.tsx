import React, { ForwardRefRenderFunction, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { LoadingIndicator, RequestStatus } from 'archilyse-ui-components';
import EditableTable, { ChangedTableType } from '../../../../components/EditableTable/EditableTable';
import { CompetitionMainCategoryResponseType, CompetitorResponseType } from '../../../../common/types';
import useCompetitorsData from './useCompetitorsData';
import CompetitorsDataUtils from './CompetitorsDataUtils';
import './buttonWithModal.scss';
import './competitorsDataModalContent.scss';

type Props = {
  competitors: CompetitorResponseType[];
  categories: CompetitionMainCategoryResponseType[];
  onClose: () => void;
  onUpload: () => void;
};

const CompetitorsDataModalContent: ForwardRefRenderFunction<any, Props> = (
  { competitors, categories, onUpload, onClose },
  _
): JSX.Element => {
  const { id: competitionId } = useParams<{ id: string }>();
  const { state, actions } = useCompetitorsData(competitionId);
  const { loaded, uploaded } = state;
  const [table, setTable] = useState<ChangedTableType>(null);

  const uploadedFeatures = React.useMemo(() => CompetitorsDataUtils.findUploadedFeatures(categories), [categories]);

  const handleSave = async () => {
    const fields = CompetitorsDataUtils.processRows(uploadedFeatures, table.rows, competitors);
    await actions.save(fields);

    onUpload();
  };

  useEffect(() => {
    actions.load(competitors);
  }, [competitors]);

  const fixedColumns = React.useMemo(() => CompetitorsDataUtils.getFixedColumns(competitors), [competitors]);
  const fixedRows = React.useMemo(() => CompetitorsDataUtils.getFixedRows(uploadedFeatures, loaded.data), [
    uploadedFeatures,
    loaded.data,
  ]);
  const rowsOptions = React.useMemo(() => CompetitorsDataUtils.getRowsOptions(uploadedFeatures), [uploadedFeatures]);

  return (
    <article className="common-modal-container">
      <main>
        <header>
          <h2>Upload competitors data</h2>
        </header>

        <div className="raw-data-uploader-container">
          <EditableTable
            onChange={setTable}
            columnsOptions={{ min: 0, max: 0 }}
            fixedColumns={fixedColumns}
            fixedRows={fixedRows}
            rowsOptions={rowsOptions}
            createNewByDefault={false}
          />
        </div>
      </main>

      <footer>
        <button className="default-button" onClick={onClose}>
          Close
        </button>
        <button className="primary-button" onClick={handleSave} disabled={uploaded.status === RequestStatus.PENDING}>
          {uploaded.status === RequestStatus.PENDING && <LoadingIndicator size={22} />}Save
        </button>
      </footer>
    </article>
  );
};

export default React.forwardRef(CompetitorsDataModalContent);
