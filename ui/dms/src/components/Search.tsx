import React, { useEffect, useState } from 'react';
import { Input, InputAdornment } from '@material-ui/core/';
import { Icon } from 'archilyse-ui-components';
import './search.scss';
import { useRouter } from 'Common/hooks';

const SEARCH_COLOR_ICON = '#8D9395';

let timeout;

const Search = ({ initialValue = undefined, onFilterChange, delay = 0 }) => {
  const { pathname } = useRouter();
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

  useEffect(() => {
    setValue('');
    onFilterChange('');
  }, [pathname]);

  return (
    <div className="search-component">
      <Input
        type="search"
        value={value}
        placeholder={'Search...'}
        disableUnderline={true}
        onChange={onChange}
        startAdornment={
          <InputAdornment className="search-icon" position="start">
            <Icon style={{ color: SEARCH_COLOR_ICON, fontWeight: '600', marginLeft: undefined }}>search</Icon>
          </InputAdornment>
        }
      />
    </div>
  );
};

export default Search;
