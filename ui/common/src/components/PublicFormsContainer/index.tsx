import React from 'react';
import C from '../../constants';
import './publicFormsContainer.scss';

const ImageLogo = ({ appTitle }) => (
  <div className="public-form-logo-container">
    <div className="public-form-logo">
      <div>
        <div className="subtitle">{appTitle}</div>
        <div className="subtitle-slogan">Business Intelligence for Architecture</div>
      </div>
    </div>
  </div>
);

const PublicFormsContainer = ({ children, appTitle = 'Archilyse.one', backgroundColor = C.COLORS.WEBSITE_BRAND }) => {
  return (
    <div className="public-form-container">
      <ImageLogo appTitle={appTitle} />
      <div className="public-form-fields-container">
        <div className="public-form-fields">
          <div>
            <div className="form-children">{children}</div>
          </div>
          <footer>
            <p>
              To learn more about Archilyse, please visit{' '}
              <a className="website-link" href="https://www.archilyse.com" target="blank">
                www.archilyse.com
              </a>
            </p>
          </footer>
        </div>
      </div>
    </div>
  );
};

export default PublicFormsContainer;
