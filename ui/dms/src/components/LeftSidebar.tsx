import React from 'react';
import { Link } from 'react-router-dom';
import { C } from 'Common';
import cookie from 'js-cookie';
import { getInitialPageUrlByRole } from 'Common/modules';
import { ProviderLocalStorage } from '../providers';
import { inView } from './DataView/modules';
import Drawer from './Drawer';
import SideBarButton from './SideBarButton';
import './leftSidebar.scss';

const onLogout = () => {
  cookie.remove(C.COOKIES.AUTH_TOKEN);
  cookie.remove(C.COOKIES.ROLES);
  ProviderLocalStorage.clear();
};

const { CLIENTS } = C.DMS_VIEWS;
const DMS_LINKS = ['/clients', '/sites', '/buildings', '/floors', '/units', '/rooms', '/room'];

const LeftSidebar = ({ pathname, clientId }) => {
  return (
    <Drawer>
      <div className="selected-view-left-sidebar">
        <div className="sidebar-buttons">
          <Link to={getInitialPageUrlByRole()}>
            <SideBarButton
              title={'Documents'}
              icon={'window'}
              active={DMS_LINKS.includes(pathname) ? true : false}
              collapsed={false}
            />
          </Link>
        </div>

        <div className="sidebar-navigation-container">
          {!inView([CLIENTS], pathname) && (
            <Link to={C.URLS.TRASH_BY_CLIENT(clientId)}>
              <SideBarButton
                title={'Trash'}
                icon={'delete'}
                active={pathname === '/trash' ? true : false}
                collapsed={false}
              />
            </Link>
          )}
          <Link to={C.URLS.PROFILE()}>
            <SideBarButton
              title={'Settings'}
              icon={'settings'}
              active={pathname === '/profile' ? true : false}
              collapsed={false}
            />
          </Link>
          <Link to={C.URLS.LOGIN()} onClick={() => onLogout()}>
            <SideBarButton title={'Logout'} icon={'logout'} active={false} collapsed={false} />
          </Link>
        </div>
      </div>
    </Drawer>
  );
};

export default LeftSidebar;
