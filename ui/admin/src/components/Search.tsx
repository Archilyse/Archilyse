import React, { useState } from 'react';
import { Input, InputAdornment } from '@material-ui/core/';
import { Icon } from 'archilyse-ui-components';
import './search.scss';

let timeout;

const Search = ({ initialValue = undefined, onFilterChange, delay = 0 }) => {
  const [value, setValue] = useState(initialValue);

  const onChange = event => {
    const { value = '' } = event.target;
    setValue(value);

    // Delay to avoid multiple renders if needed
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      onFilterChange(value);
    }, delay);
  };

  return (
    <div className="search-component">
      <Input
        type="search"
        value={value}
        onChange={onChange}
        inputProps={{
          name: 'search-input',
        }}
        startAdornment={
          <InputAdornment className="search-icon" position="start">
            <Icon style={{ color: 'inherit', marginLeft: undefined }}>search</Icon>
          </InputAdornment>
        }
      />
    </div>
  );
};

export default Search;
