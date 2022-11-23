import React from 'react';
import { Icon } from 'archilyse-ui-components';
import { TextField } from '@material-ui/core';
import { Autocomplete } from '@material-ui/lab';
import Tag from './Tag';
import './tags.scss';

const Tags = ({
  value,
  onChange,
  editable,
  suggestions,
  disablePortal = true,
  freeSolo = true,
  getOptionLabel = undefined,
}) => {
  const optionalProps = { getOptionLabel };
  return (
    <Autocomplete
      disablePortal={disablePortal}
      multiple
      limitTags={3}
      classes={{ root: 'autocomplete', option: 'autocomplete-option' }}
      id="item-tags"
      options={suggestions}
      value={value}
      onChange={onChange}
      freeSolo={freeSolo}
      renderTags={(value, getTagProps) =>
        value.map((option, index) => (
          <Tag
            key={option}
            label={getOptionLabel ? getOptionLabel(option) : option}
            chipProps={{ ...getTagProps({ index }) }}
          />
        ))
      }
      renderInput={params => {
        const InputProps: any = {
          ...params.InputProps,
          disableUnderline: !editable,
          startAdornment: (
            <>
              {params.InputProps.startAdornment}
              <Icon data-testid="tags-add-circle-icon" className="tags-add-circle-icon" style={{ fontSize: 20 }}>
                add_circle
              </Icon>
            </>
          ),
        };
        params.InputProps = InputProps;
        params.inputProps = {
          ...params.inputProps,
          'data-testid': 'tags-text-field',
        };
        return (
          <>
            <TextField name="labels" className="autocomplete-input" {...params} />
          </>
        );
      }}
      {...optionalProps}
    />
  );
};

export default Tags;
