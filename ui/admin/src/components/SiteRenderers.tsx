import React, { useContext, useState } from 'react';
import { SnackbarContext } from 'archilyse-ui-components';
import { Button, Checkbox, FormControl, MenuItem, Select } from '@material-ui/core';
import { ProviderRequest } from '../providers';
import { getFile, isSiteSimulated } from '../common/modules';
import { C } from '../common';
import './siteRenderers.scss';
import FileUploadRenderer from './FileUploadRenderer';

const generateFeatures = async (snackbar, id) => {
  try {
    await ProviderRequest.post(C.ENDPOINTS.SITE_RUN_FEATURES(id), {});
    snackbar.show({
      message: `Successfully started running analysis for site with id [${id}]`,
      severity: 'success',
    });
  } catch (error) {
    const customMessage = error.response && error.response.data && error.response.data.msg;
    snackbar.show({
      message: customMessage || 'Some requirements are not met for the site requested',
      severity: 'error',
    });
    console.log('Error trying to start feature generation', error);
  }
};

export default (classes, groups, classification_schemes) => {
  const MarkAsDeliveredRenderer = ({ data }) => {
    const [checked, setChecked] = useState(Boolean(data.delivered));

    const snackbar = useContext(SnackbarContext);

    const changeCheckboxStatus = async () => {
      const newChecked = !checked;
      setChecked(newChecked);

      try {
        await ProviderRequest.put(C.ENDPOINTS.SITE_BY_ID(data.id), { delivered: newChecked });
      } catch (error) {
        snackbar.show({ message: `Error saving delivered status: ${error}`, severity: 'error' });
      }
    };

    return (
      <Checkbox
        checked={checked}
        color="primary"
        className={`site-delivered-${checked}`}
        onChange={changeCheckboxStatus}
        value="primary"
        inputProps={{ 'aria-label': 'primary checkbox' }}
      />
    );
  };

  const GenerateFeaturesRenderer = ({ data }) => {
    const [disabled, setDisabled] = useState(false);

    const snackbar = useContext(SnackbarContext);

    const color = isSiteSimulated(data) ? undefined : 'primary';

    const onClick = async () => {
      setDisabled(true);
      await generateFeatures(snackbar, data.id);
      setDisabled(false);
    };

    return (
      <div className="features-button">
        <Button
          variant="contained"
          className="generate-features-button"
          disabled={disabled}
          color={color}
          onClick={onClick}
        >
          {isSiteSimulated(data) ? 'Re-run' : 'Run'}
        </Button>
      </div>
    );
  };

  const DownloadZipRenderer = ({ data }) => {
    const snackbar = useContext(SnackbarContext);

    const onClick = async () => {
      try {
        const response = await ProviderRequest.getFiles(
          `/site/${data.id}/deliverable/download`,
          C.RESPONSE_TYPE.ARRAY_BUFFER
        );
        await getFile(response, `deliverable_${data.id}.zip`, C.MIME_TYPES.ZIP);
      } catch (error) {
        const decodedString = String.fromCharCode.apply(null, new Uint8Array(error.response.data));
        const errorMessage = JSON.parse(decodedString)['msg'];
        snackbar.show({ message: `${errorMessage}`, severity: 'error' });
      }
    };
    if (!isSiteSimulated(data)) return '';
    return (
      <Button variant="contained" className="" onClick={onClick}>
        Zip
      </Button>
    );
  };

  const GroupSelectorRenderer = ({ data }) => {
    const [groupID, setGroupID] = useState(data.group_id);

    const snackbar = useContext(SnackbarContext);

    const changeGroup = async (event, data) => {
      setGroupID(event.target.value);
      try {
        await ProviderRequest.put(C.ENDPOINTS.SITE_BY_ID(data.id), { group_id: event.target.value });
      } catch (error) {
        snackbar.show({ message: `Error saving group: ${error}`, severity: 'error' });
      }
    };

    return (
      <FormControl className={classes.formControl}>
        <Select onChange={event => changeGroup(event, data)} value={groupID != null ? groupID : ''}>
          <MenuItem value={null}>-</MenuItem>
          {groups.map(group => (
            <MenuItem key={group.id} value={group.id}>
              {group.name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    );
  };

  const ClassificationSchemeSelectorRenderer = ({ data }) => {
    const [schemeName, setschemeName] = useState(data.classification_scheme);

    const snackbar = useContext(SnackbarContext);

    const changeScheme = async (event, data) => {
      setschemeName(event.target.value);
      try {
        await ProviderRequest.put(C.ENDPOINTS.SITE_BY_ID(data.id), { classification_scheme: event.target.value });
      } catch (error) {
        snackbar.show({ message: `Error saving classification_scheme: ${error}`, severity: 'error' });
      }
    };

    return (
      <FormControl className={classes.formControl}>
        <Select onChange={event => changeScheme(event, data)} value={schemeName != null ? schemeName : ''}>
          {classification_schemes.map(classification_scheme => (
            <MenuItem key={classification_scheme} value={classification_scheme}>
              {classification_scheme}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    );
  };

  const CustomValuatorRenderer = ({ data }) => {
    const snackbar = useContext(SnackbarContext);

    function successHandler() {
      snackbar.show({ message: 'File uploaded successfully.', severity: 'success' });
    }

    function errorHandler(error) {
      console.error(error);
      let message = error?.response?.data?.msg;
      if (!message) {
        // handle marshmallow validation error
        if (error?.response?.data.errors?.files?.custom_valuator_results) {
          message = JSON.stringify(error.response.data.errors.files.custom_valuator_results);
        } else {
          message = 'Wrong file format, check the browser console (F12)';
        }
      }

      snackbar.show({ message, severity: 'error' });
    }
    return (
      <FileUploadRenderer
        id="ph_results_file_upload"
        onSuccess={successHandler}
        onError={errorHandler}
        name="custom_valuator_results"
        url={C.ENDPOINTS.SITE_UPLOAD_PH_RESULTS(data.id)}
      />
    );
  };

  return {
    GenerateFeaturesRenderer,
    MarkAsDeliveredRenderer,
    DownloadZipRenderer,
    GroupSelectorRenderer,
    ClassificationSchemeSelectorRenderer,
    CustomValuatorRenderer,
  };
};
