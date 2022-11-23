import React, { useState } from 'react';
import { Tags } from 'Components';
import { FormControl, FormHelperText, MenuItem, Select } from '@material-ui/core';
import { C } from 'Common';
import { DMSPermissions } from 'Common/types';
import { capitalize } from 'archilyse-ui-components';
import './ruleForm.scss';

const { READ_ALL, EDIT_ALL } = C.DMS_PERMISSIONS;
const RuleForm = ({ onSubmit, suggestedSites, onClose }) => {
  const [sites, setSites] = useState([]);
  const [permission, setPermission] = useState<DMSPermissions | ''>('');
  const [missingPermission, setMissingPermission] = useState(false);
  const [missingSite, setMissingSites] = useState(false);

  const allSelected = permission === READ_ALL || permission === EDIT_ALL;

  const onClickAdd = () => {
    const sitesSelected = sites && sites.length;
    const isFormValid = Boolean(permission && sitesSelected) || Boolean(!sitesSelected && allSelected);

    if (isFormValid) {
      onSubmit({ permission, sites });

      setSites([]);
      setMissingPermission(false);
      setMissingSites(false);
      setPermission('');
    } else {
      if (!permission) {
        setMissingPermission(true);
      }
      if (!sitesSelected) {
        setMissingSites(true);
      }
    }
  };

  const onSelectPermission = event => {
    setPermission(event.target.value);
  };
  return (
    <>
      <div className="permissions-field">
        <FormControl error={missingPermission} className="permissions-input">
          <label>Permission</label>
          <Select
            id={'permissions-dropdown'}
            value={permission}
            inputProps={{ 'data-testid': 'permissions-dropdown' }}
            onChange={onSelectPermission}
          >
            {Object.entries(C.DMS_PERMISSIONS).map(([label, value]) => (
              <MenuItem key={value} value={value}>
                <div>{capitalize(label.toLowerCase().replace('_', ' '))}</div>
              </MenuItem>
            ))}
          </Select>
          {missingPermission && <FormHelperText>Please add a permission</FormHelperText>}
        </FormControl>
      </div>
      <div className="site-permissions-field">
        <FormControl error={missingSite} className="permissions-input">
          <label>Sites</label>
          {allSelected ? (
            <p>This will give the user {permission === READ_ALL ? 'read' : 'edit'} permissions in every site</p>
          ) : (
            <Tags
              onChange={(event, value) => setSites(value)}
              value={sites}
              suggestions={suggestedSites}
              getOptionLabel={option => option.name}
              disablePortal={false}
              freeSolo={false}
              editable
            />
          )}
          {missingSite && <FormHelperText>Please add at least one site</FormHelperText>}
        </FormControl>
      </div>

      <div className="action-buttons">
        <div className="cancel-button">
          <button
            id="save-permissions"
            data-testid="close-button"
            className="primary-button cancel-button"
            onClick={onClose}
            type="button"
          >
            Cancel
          </button>
        </div>
        <div className="submit-button">
          <button id="save-permissions" className="primary-button save-button" onClick={onClickAdd}>
            Save
          </button>
        </div>
      </div>
    </>
  );
};

export default RuleForm;
