import React, { useEffect, useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import {
  Checkbox,
  Chip,
  FormControl,
  FormControlLabel,
  FormLabel,
  InputAdornment,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Tooltip,
} from '@material-ui/core';
import { passwordStrength } from 'check-password-strength';
import Icon from '../Icon';
import { usePrevious } from '../../hooks';
import './form.scss';

const DEFAULT_TYPE = 'text';
const DEFAULT_SUBMIT_TEXT = 'Save';

const ALLOWED_SPECIAL_CHARACTERS = '!@#$%^&*,.¿?-_¡<>^+';
const renderMultipleValues = (values: any, field) => {
  if (!field.options || !field.options.length) {
    return null;
  }
  const getLabel = (value, field) => {
    const correctOption = field.options.find(option => option.value === value);
    return correctOption && correctOption.label;
  };
  return (
    <div>
      {values.map(value => (
        <Chip key={value} label={getLabel(value, field)} />
      ))}
    </div>
  );
};

const Password = ({ field, errors, setValue, watch, register, getValues, separatedLabels }) => {
  const [isVisible, setIsVisible] = useState(false);

  const { password } = getValues();
  const strengthOptions = undefined; // So the library use the default ones
  const strength = passwordStrength(password, strengthOptions, ALLOWED_SPECIAL_CHARACTERS);

  const isPasswordValid = () => strength.value === 'Medium' || strength.value === 'Strong';
  const validatePassword = () => {
    if (!isPasswordValid()) return 'Password not valid';
  };

  const meetsRule = rule => strength.contains.includes(rule);

  const getHelperText = (errors, field) => {
    if (field.validate) return errors?.[field.name]?.message;
    if (!password) return null;
    if (field.passwordValidation) {
      return (
        <ul className="password-rules" style={{ padding: '5px' }}>
          <li style={{ color: meetsRule('lowercase') ? 'green' : '' }}>One lowercase character</li>
          <li style={{ color: meetsRule('uppercase') ? 'green' : '' }}>One uppercase character</li>
          <li style={{ color: meetsRule('symbol') ? 'green' : '' }}>One special character</li>
          <li style={{ color: meetsRule('number') ? 'green' : '' }}>One number</li>
          <li style={{ color: password?.length >= 8 ? 'green' : '' }}>8 characters minimum</li>
        </ul>
      );
    }
  };

  const getValidation = field => {
    if (field.passwordValidation && password) return validatePassword();
    if (field.validate) return field.validate(getValues());
    return true;
  };

  const togglePassword = () => setIsVisible(!isVisible);
  return (
    <TextField
      className={field.className}
      fullWidth={true}
      color={field.color}
      id={field.id ? field.id : field.name}
      data-testid={isPasswordValid() ? 'valid-password' : 'invalid-password'}
      name={field.name}
      label={!separatedLabels ? field.label : null}
      required={field.required}
      inputRef={register({
        validate: () => getValidation(field),
      })}
      disabled={field.disabled}
      placeholder={field.placeholder}
      value={watch(field.name)}
      onChange={event => setValue(field.name, event.target.value, { shouldValidate: true, shouldDirty: true })}
      InputProps={{
        endAdornment: (
          <Tooltip title={isVisible ? 'Hide password ' : 'Show password'}>
            <InputAdornment
              position="end"
              onClick={togglePassword}
              data-testid="toggle-visibility-icon"
              style={{ cursor: 'pointer' }}
            >
              <Icon>{isVisible ? 'visibility_off' : 'visibility'}</Icon>
            </InputAdornment>
          </Tooltip>
        ),
        ...field.InputProps,
      }}
      type={isVisible ? 'text' : 'password'}
      error={Boolean(errors?.[field.name])}
      helperText={getHelperText(errors, field)}
    />
  );
};
const Dropdown = ({ field, value, control }) => {
  const renderValue = field.multiple ? values => renderMultipleValues(values, field) : undefined;
  return (
    <FormControl fullWidth>
      {field.label && <InputLabel>{field.label}</InputLabel>}
      <Controller
        control={control}
        name={field.name}
        rules={{ required: field.required }}
        defaultValue={value[field.name] || (field.multiple ? [] : '')}
        as={
          <Select className={`form-select-${field.name}`} multiple={field.multiple} renderValue={renderValue}>
            {field.options.map(option => (
              <MenuItem key={`${option.value} - ${option.label}`} value={option.value}>
                <div>{option.label}</div>
              </MenuItem>
            ))}
          </Select>
        }
      />
    </FormControl>
  );
};

const renderIfVisible = (field, getValues) => component => {
  if ('visible' in field) {
    return field.visible(getValues()) ? component : null;
  }

  return component;
};

type Props = {
  fields: any[];
  onSubmit: (values) => void;
  onChange?: (values) => void;
  onCancel?: () => void;
  value?: any;
  buttonDisabledStatus?: boolean;
  SubmitButton?: React.ComponentType;
  submitText?: string;
  watch?: string[];
  separatedLabels?: boolean;
  showCancelButton?: boolean;
  submitButtonId?: string;
  id?: string;
};

const Form = ({
  fields,
  onSubmit,
  value = {},
  onChange = (formValues: any) => {},
  onCancel = () => {},
  buttonDisabledStatus = false,
  SubmitButton = null,
  submitText = DEFAULT_SUBMIT_TEXT,
  watch: trackedFields = null,
  separatedLabels = false,
  showCancelButton = false,
  submitButtonId = '',
  id = '',
}: Props) => {
  const { register, control, handleSubmit, getValues, errors, setValue, watch } = useForm({ defaultValues: value });
  if (trackedFields) {
    watch(trackedFields);
  }

  const previousValue = usePrevious(value);

  const handleChange = event => {
    const formValues = getValues();
    onChange(formValues);
  };

  // If prop value changes, update internal form state
  const updateInternalFormValue = value => {
    Object.keys(value)
      .filter(key => value[key] !== previousValue[key])
      .forEach(key => {
        setValue(key, value[key], { shouldValidate: true, shouldDirty: true });
      });
  };
  useEffect(() => {
    updateInternalFormValue(value);
  }, [value]);

  return (
    <form id={id} className="form" onSubmit={handleSubmit(onSubmit)} onChange={handleChange}>
      {fields.map(field => {
        const render = renderIfVisible(field, getValues);

        if (field.type === 'file') {
          return (
            <div className="field" key={field.name}>
              <FormLabel>{field.label}</FormLabel>
              <input
                ref={register}
                id={field.name}
                name={field.name}
                required={field.required}
                type="file"
                accept={field.accept}
                disabled={field.disabled || false}
                multiple={field.multiple}
              />
            </div>
          );
        } else if (field.type == 'dropdown') {
          return (
            <div className={`field${separatedLabels ? ' separated-label' : ''}`} key={field.name}>
              {separatedLabels && <label>{field.label}</label>}
              <Dropdown field={separatedLabels ? { ...field, label: null } : field} value={value} control={control} />
            </div>
          );
        } else if (field.type == 'label') {
          return render(<div className={field.class}>{field.label}</div>);
        } else if (field.type == 'checkbox') {
          return (
            <div className={`field${separatedLabels ? ' separated-label' : ''}`} key={field.name}>
              <FormControlLabel
                control={
                  <Checkbox
                    name={field.name}
                    checked={watch(field.name)}
                    onChange={event => {
                      setValue(field.name, event.target.checked);
                    }}
                    inputRef={register({})}
                  />
                }
                label={field.label}
                title={field.title}
              />
            </div>
          );
        } else if (field.type == 'password') {
          return render(
            <div className={`field${separatedLabels ? ' separated-label' : ''}`} key={field.name}>
              {separatedLabels && <label>{field.label}</label>}
              <Password
                field={field}
                errors={errors}
                setValue={setValue}
                watch={watch}
                register={register}
                getValues={getValues}
                separatedLabels={separatedLabels}
              />
            </div>
          );
        }
        return render(
          <div className={`field${separatedLabels ? ' separated-label' : ''}`} key={field.name}>
            {separatedLabels && <label>{field.label}</label>}
            <TextField
              fullWidth={true}
              className={field.className}
              color={field.color}
              id={field.id || field.name}
              name={field.name}
              label={!separatedLabels ? field.label : null}
              required={field.required}
              inputRef={register({
                validate: () => (field.validate ? field.validate(getValues()) : true),
              })}
              disabled={field.disabled}
              placeholder={field.placeholder}
              value={watch(field.name)}
              onChange={event => setValue(field.name, event.target.value, { shouldValidate: true, shouldDirty: true })}
              inputProps={field.InputProps}
              type={field.type || DEFAULT_TYPE}
              error={Boolean(errors?.[field.name])}
              helperText={errors?.[field.name]?.message}
            />
          </div>
        );
      })}
      <br />
      <p />
      <div className="action-buttons">
        {showCancelButton ? (
          <div className="cancel-button">
            <button className="primary-button cancel-button" onClick={() => onCancel()} type="button">
              Cancel
            </button>
          </div>
        ) : null}
        {SubmitButton ? (
          <SubmitButton />
        ) : (
          <div className="submit-button">
            <button
              className="primary-button save-button"
              disabled={buttonDisabledStatus}
              id={submitButtonId}
              type="submit"
            >
              {submitText}
            </button>
          </div>
        )}
      </div>
    </form>
  );
};

export default Form;
