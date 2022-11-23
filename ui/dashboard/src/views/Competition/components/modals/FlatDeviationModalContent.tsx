import React, { ForwardRefRenderFunction } from 'react';
import { LoadingIndicator, RequestStatus } from 'archilyse-ui-components';
import CompetitionConfigurationTable from './CompetitionConfigurationTable';
import useFieldsValidation from './useFieldsValidation';
import useConfigurationParamsData from './useConfigurationParamsData';
import './buttonWithModal.scss';

type Props = {
  onClose: () => void;
};

const FlatDeviationModalContent: ForwardRefRenderFunction<any, Props> = ({ onClose }, _): JSX.Element => {
  const { params, updated, updateData, saveData } = useConfigurationParamsData({
    field: 'flat_types_distribution',
  });
  const data = params.data.flat_types_distribution || [];
  const { errors, validateFields, hasErrors } = useFieldsValidation();

  const handleSave = async () => {
    const newErrors = validateFields(data);

    if (hasErrors(newErrors)) return;

    saveData();
  };

  return (
    <article className="common-modal-container">
      <main>
        <header>
          <h2>Flat Deviation</h2>
        </header>

        <div className="table-container">
          <CompetitionConfigurationTable
            data={data}
            onChange={updateData}
            errors={errors}
            loading={params.status === RequestStatus.PENDING && <LoadingIndicator />}
          />
        </div>
      </main>

      <footer>
        <button className="default-button" onClick={onClose}>
          Close
        </button>
        <button className="primary-button" onClick={handleSave} disabled={updated.status === RequestStatus.PENDING}>
          {updated.status === RequestStatus.PENDING ? <LoadingIndicator size={25} /> : 'Apply'}
        </button>
      </footer>
    </article>
  );
};

export default React.forwardRef(FlatDeviationModalContent);
