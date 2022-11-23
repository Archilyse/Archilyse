import ToggleButton from '@material-ui/lab/ToggleButton';
import ToggleButtonGroup from '@material-ui/lab/ToggleButtonGroup';
import React, { useContext } from 'react';
import Expandable from '../Expandable';
import './collapseToggles.scss';

type Props = {
  options: { label: string; value: string }[];
};

const COLLAPSE_ALL_VALUE = '';

const CollapseToggles = ({ options }: Props): JSX.Element => {
  const { expandedCategories, onExpand } = useContext(Expandable.Context);

  const handleChange = (event: React.MouseEvent<HTMLButtonElement>) => {
    const clickedCategory = event.currentTarget.value;

    if (clickedCategory === COLLAPSE_ALL_VALUE) {
      onExpand([]);
    } else {
      // subcategories and data-features have 'category.xxx' names
      const subCategories = expandedCategories.filter(category => category.startsWith(clickedCategory + '.'));

      onExpand([clickedCategory, ...subCategories]);
    }
  };

  const mainCategories = expandedCategories.filter(category => !category.includes('.'));

  return (
    <div className="collapse-toggles-container">
      <ToggleButtonGroup
        value={mainCategories}
        onChange={handleChange}
        aria-label="group of collapse buttons"
        size="small"
      >
        <ToggleButton value={COLLAPSE_ALL_VALUE} aria-label="Collapse all">
          Register zuklappen
        </ToggleButton>
        {options.map(option => (
          <ToggleButton key={option.value} value={option.value} aria-label={option.label}>
            {option.label}
          </ToggleButton>
        ))}
      </ToggleButtonGroup>
    </div>
  );
};

export default CollapseToggles;
