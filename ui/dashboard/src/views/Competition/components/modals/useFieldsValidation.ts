import { useState } from 'react';
import { FlatDeviationResponseType } from '../../../../common/types';
import { CompetitionConfigurationTableErrors } from './CompetitionConfigurationTable';

const getDecimalPart = n => n - Math.floor(n);
const validateFields = (fields: FlatDeviationResponseType[]): CompetitionConfigurationTableErrors[] => {
  return fields.map(field => ({
    apartment_type: [0, 0.5].includes(getDecimalPart(field.apartment_type))
      ? null
      : 'Value can only be either an integer (1-7) or decimal with .5 at the end',
  }));
};
const hasErrors = fields => {
  return fields.some(field => Object.values(field).filter(Boolean).length > 0);
};

const useFieldsValidation = () => {
  const [errors, setErrors] = useState<CompetitionConfigurationTableErrors[]>([]);

  const handleValidate = newFields => {
    const newErrors = validateFields(newFields);
    setErrors(newErrors);

    return newErrors;
  };

  return { errors, hasErrors, validateFields: handleValidate };
};

export default useFieldsValidation;
