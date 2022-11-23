import React from 'react';
import { CompetitionMainCategoryResponseType } from '../../../../common/types';
import { Can } from '../../../../components';
import { getSafePercents } from '../utils';
import InputWithIcon from './InputWithIcon';
import './weight.scss';

const ICON_SIZE = 16;

type Props = {
  weight: number;
  category: CompetitionMainCategoryResponseType;
  onChange: (categoryKey: string, value: string | number) => void;
};

const Weight = ({ weight, category, onChange }: Props): JSX.Element => {
  const [formattedPercents, percents] = getSafePercents(weight);

  return (
    <div className="weight">
      <div className="weight-main">
        <p>{category.name}</p>
        <Can
          perform="competition:change-weights"
          yes={() => (
            <InputWithIcon
              text={formattedPercents}
              value={percents}
              onSave={value => onChange(category.key, value)}
              inputProps={{ name: 'editable-weight', max: 100 }}
              iconSize={ICON_SIZE}
            />
          )}
          no={() => <span>{formattedPercents}</span>}
        />
      </div>
      <div>
        <div className="progress-bar">
          <span style={{ width: formattedPercents }} />
        </div>
      </div>
    </div>
  );
};

export default Weight;
