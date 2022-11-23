import React, { useEffect, useState } from 'react';
import { Breadcrumbs } from '@material-ui/core';
import { Icon } from 'archilyse-ui-components';
import { Link } from 'react-router-dom';
import { useWindowSize } from 'Common/hooks';
import Truncate from './Truncate';
import './breadcrumb.scss';

const navigationArrowWidth = 28;

const Breadcrumb = ({ hierarchy = [] }) => {
  const [maxWidth, setMaxWidth] = useState(0);
  const [breadcrumbRef, setBreadcrumbRef] = useState<HTMLElement>();
  const [currentHierarchy, setCurrentHierarchy] = useState(hierarchy);
  const { width } = useWindowSize();

  useEffect(() => {
    const parentWidth = breadcrumbRef?.parentElement?.offsetWidth;
    if (currentHierarchy.length > 0 && parentWidth) {
      setMaxWidth(parentWidth / currentHierarchy.length - navigationArrowWidth);
    }
  }, [currentHierarchy.length, breadcrumbRef, width]);

  useEffect(() => {
    if (hierarchy.length > 0) setCurrentHierarchy([...hierarchy]);
  }, [hierarchy]);

  return (
    <Breadcrumbs
      ref={setBreadcrumbRef}
      aria-label="breadcrumb"
      separator={<Icon style={{ marginLeft: 0, fontSize: 20 }}>fslash</Icon>}
    >
      {currentHierarchy.map((link, index) => {
        if (index === currentHierarchy.length - 1)
          return (
            <a key={link.text} className="breadcrumb-link active-link">
              <Truncate maxWidth={maxWidth}>{link.text}</Truncate>
            </a>
          );
        return (
          <Link key={link.text} to={link.href} className="breadcrumb-link">
            <Truncate maxWidth={maxWidth}>{link.text}</Truncate>
          </Link>
        );
      })}
    </Breadcrumbs>
  );
};

export default Breadcrumb;
