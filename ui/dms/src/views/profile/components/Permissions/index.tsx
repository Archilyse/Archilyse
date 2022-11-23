import React, { useContext, useEffect, useState } from 'react';
import { Icon, SnackbarContext } from 'archilyse-ui-components';
import { Search, Tag } from 'Components';
import { Drawer } from '@material-ui/core';
import { ProviderRequest } from 'Providers';
import { C } from 'Common';
import { Rule, Rules } from 'Common/types';
import { compileUserRules, getRuleName, parseBackendRules } from './modules';
import RuleForm from './RuleForm';
import './permissions.scss';

// @TODO: Spinner on loading data
// @TODO: Color while adding the rule should be the same as in the final one

const EDIT_ICON_COLOR = '#434C50';
const { DMS_PERMISSIONS, ROLES } = C;

const ROLE_LABELS = {
  [ROLES.ARCHILYSE_ONE_ADMIN]: 'Admin',
  [ROLES.DMS_LIMITED]: 'User',
};

const { READ_ALL, EDIT_ALL } = DMS_PERMISSIONS;
const RulesComponent = ({ userId, rules, onDeleteRule }) => {
  if (!rules || !rules[userId]?.length) {
    return <p>No permissions assigned yet</p>;
  }
  return rules[userId]?.map(rule => (
    <Tag key={getRuleName(rule)} label={getRuleName(rule)} chipProps={{ onDelete: () => onDeleteRule(userId, rule) }} />
  ));
};

const Permissions = ({ users, sites, permissions }) => {
  const [rules, setRules] = useState<Rules>({});
  const [showEditUserDrawer, setShowEditUserDrawer] = useState<boolean>(false);
  const [selectedUserID, setSelectedUserID] = useState<string>('');
  const [showSnackBar, setShowSnackBar] = useState<boolean>(false);
  const [searchValue, setSearchValue] = useState<string>('');

  const toggleEditUserDrawer = (userID, showEditUserDrawer: boolean) => {
    setSelectedUserID(userID);
    setShowEditUserDrawer(showEditUserDrawer);
  };

  const onFilterChange = value => {
    const filter = value.toLowerCase();
    setSearchValue(filter || '');
  };

  const filteredUsers = users.filter(user => user.name.toLowerCase().indexOf(searchValue) > -1);

  const snackbar = useContext(SnackbarContext);

  useEffect(() => {
    const newRules = parseBackendRules(permissions, sites);
    setRules(newRules);
  }, [permissions]);

  useEffect(() => {
    onSavePermissions();
  }, [rules]);

  // @TODO: If we already have ALL and add something, we should erase the ALL
  // @TODO: Filter duplicated rules
  const onSubmitNewRule = (userId: string, newRule: Rule) => {
    setShowSnackBar(true);
    const userRules = rules[userId] || [];
    const { permission } = newRule;
    const newRules = permission === READ_ALL || permission === EDIT_ALL ? [newRule] : [...userRules, newRule];
    const newUserRules = { [userId]: newRules };
    setRules({ ...rules, ...newUserRules });
  };

  const onDeleteRule = (userId, ruleToDelete) => {
    setShowSnackBar(true);
    const filteredUserRules = rules[userId].filter(rule => getRuleName(rule) !== getRuleName(ruleToDelete));
    const newUserRules = { [userId]: filteredUserRules };
    setRules({ ...rules, ...newUserRules });
  };

  // @TODO For now we send all permissions, this could be improved sending only modified ones
  const onSavePermissions = async () => {
    const requests = Object.entries(rules).map(([userId, userRules]) => {
      const backendUpdateRules = compileUserRules(userRules);
      return ProviderRequest.put(C.ENDPOINTS.USER_DMS_PERMISSIONS(userId), backendUpdateRules);
    });
    try {
      await Promise.all(requests);
      if (showSnackBar) snackbar.show({ message: 'Permissions updated successfully', severity: 'success' });
    } catch (error) {
      console.log('Error updating permissions', error);
      snackbar.show({
        message: 'Error updating permissions, please contact support',
        severity: 'error',
      });
      throw error; // We want the errors to arrive to sentry at the beginning
    }
    setShowSnackBar(false);
  };

  return (
    <>
      <Drawer anchor={'right'} open={showEditUserDrawer} onClose={() => toggleEditUserDrawer(selectedUserID, false)}>
        <div className="create-user-container">
          <div className="create-user-header">
            <h3 className="create-user-title">Edit user</h3>
            <button
              data-testid="close-icon"
              className="close-button"
              onClick={() => toggleEditUserDrawer(selectedUserID, false)}
            >
              <Icon style={{ marginLeft: '0', fontSize: '24px' }}>close</Icon>
            </button>
          </div>

          <>
            <h4>Add permissions</h4>
            <div className="user-profile-container">
              <RuleForm
                onSubmit={(rule: Rule) => onSubmitNewRule(selectedUserID, rule)}
                suggestedSites={sites}
                onClose={toggleEditUserDrawer}
              />
            </div>
          </>
        </div>
      </Drawer>

      <div className="users-permissions-container">
        <>
          <Search
            initialValue={searchValue}
            onFilterChange={onFilterChange}
            delay={(users || []).length > 100 ? C.DELAY_FILTER_MS : 0}
          />
          <div className="header-hseparator" />
        </>
        <>
          {!users.length && <p className="no-users-message">There are no users created yet.</p>}
          {users.length > 0 && (
            <table aria-label="simple table">
              <thead>
                <tr>
                  <th>Full name</th>
                  <th>Email address</th>
                  <th>Role</th>
                  <th>Permissions</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map(user => (
                  <tr key={user.id}>
                    <td>
                      <div className="user-name">
                        <Icon style={{ marginLeft: '0', marginRight: '10px', fontSize: '30px' }}>portrait</Icon>
                        {user.name}
                      </div>
                    </td>
                    <td>{user.email}</td>
                    <td>{ROLE_LABELS[user.roles]}</td>
                    <td>
                      <RulesComponent userId={user.id} rules={rules} onDeleteRule={onDeleteRule} />
                    </td>
                    <td className="add-permissions">
                      <button
                        className="button add-permissions-button create-user-button"
                        onClick={() => toggleEditUserDrawer(user.id, true)}
                      >
                        <Icon
                          style={{ marginLeft: '0', marginRight: '10px', fontSize: '20px', color: EDIT_ICON_COLOR }}
                        >
                          lockopen
                        </Icon>
                        Add permission
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      </div>
    </>
  );
};

export default Permissions;
