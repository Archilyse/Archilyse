import React, { useState } from 'react';
import useSWR from 'swr';
import { auth, capitalize, Icon } from 'archilyse-ui-components';
import { LeftSidebar } from 'Components';
import { Drawer } from '@material-ui/core';
import { UserModel } from '../../common/types';
import { ProviderRequest } from '../../providers';
import { C } from '../../common';
import { CreateUser, General, Permissions } from './components';
import './profile.scss';

const EDIT_ICON_COLOR = '#434C50';
const CREATE_USER_ICON_COLOR = '#FFFFFF';

const ManageUsers = ({ toggleCreateUserDrawer }) => (
  <div>
    <div className="manage-user-header">
      <div className="search-users">
        <h4>User management</h4>
      </div>
      <button
        aria-label="create user"
        className="button manage-user-button create-user-button"
        onClick={() => toggleCreateUserDrawer(true)}
      >
        <Icon style={{ marginRight: '8px', marginLeft: '0px', fontSize: '20px', color: CREATE_USER_ICON_COLOR }}>
          addcircle
        </Icon>
        Create user
      </button>
    </div>
  </div>
);

const isDMSAdmin = () => auth.getRoles().includes(C.ROLES.ARCHILYSE_ONE_ADMIN);

const getSitesEndpoint = clientId => (isDMSAdmin() ? C.ENDPOINTS.SITES_BY_CLIENT(clientId) : null);
const getUserEndpoint = clientId => (isDMSAdmin() ? C.ENDPOINTS.USERS_BY_CLIENT(clientId) : null);
const getPermissionsEndpoint = () => (isDMSAdmin() ? C.ENDPOINTS.USER_DMS_PERMISSIONS() : null);
// @TODO: Types in all responses
const Profile = () => {
  const { id: currentUserId, client_id: clientId } = auth.getUserInfo();
  const { data: users = [], mutate: mutateUsers } = useSWR(getUserEndpoint(clientId), ProviderRequest.get);
  const { data: sites = [] } = useSWR(getSitesEndpoint(clientId), ProviderRequest.get);
  const { data: permissions = [] } = useSWR(getPermissionsEndpoint(), ProviderRequest.get);
  const filteredUsers = users.filter(user => user.id !== currentUserId);

  const { data: user, mutate: mutateUser } = useSWR<UserModel>(C.ENDPOINTS.USER(currentUserId), ProviderRequest.get);

  const [showEditProfileDrawer, setShowEditProfileDrawer] = useState<boolean>(false);
  const [showCreateUserDrawer, setShowCreateUserDrawer] = useState<boolean>(false);

  const toggleEditProfileDrawer = (showEditProfileDrawer: boolean) => setShowEditProfileDrawer(showEditProfileDrawer);
  const toggleCreateUserDrawer = (showCreateUserDrawer: boolean) => setShowCreateUserDrawer(showCreateUserDrawer);

  return (
    <div className="profile-container">
      <LeftSidebar pathname={'/profile'} clientId={clientId} />

      <Drawer anchor={'right'} open={showEditProfileDrawer} onClose={() => toggleEditProfileDrawer(false)}>
        <General user={user} mutate={mutateUser} onCancel={toggleEditProfileDrawer} />
      </Drawer>

      <div className="general-profile-header">
        <div className="user-profile">
          <div className="user-profile-info">
            <div className="user-name">{capitalize(user?.name || '')}</div>
            <div className="user-email">{user?.email || ''}</div>
          </div>
          <button
            aria-label="edit profile"
            className="button manage-user-button edit-profile-button"
            onClick={() => toggleEditProfileDrawer(true)}
          >
            <Icon style={{ marginRight: '8px', marginLeft: '0px', fontSize: '18px', color: EDIT_ICON_COLOR }}>
              edit
            </Icon>
            Edit profile
          </button>
        </div>

        <div className="header-hseparator" />
      </div>

      {isDMSAdmin() && (
        <>
          <ManageUsers toggleCreateUserDrawer={toggleCreateUserDrawer} />
          <Drawer anchor={'right'} open={showCreateUserDrawer} onClose={() => toggleCreateUserDrawer(false)}>
            <CreateUser onCreateUser={mutateUsers} onCancel={toggleCreateUserDrawer} />
          </Drawer>
          <Permissions users={filteredUsers} sites={sites} permissions={permissions} />
        </>
      )}
    </div>
  );
};

export default Profile;
