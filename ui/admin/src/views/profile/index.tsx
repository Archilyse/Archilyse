import React from 'react';
import { LeftSidebar, PaperCard } from 'Components';
import { General } from './components';
import './profile.scss';

const Profile = () => {
  return (
    <div className="profile-container">
      <LeftSidebar buttons={null} bottomContent={null} />
      <PaperCard title="General">
        <General />
      </PaperCard>
    </div>
  );
};

export default Profile;
