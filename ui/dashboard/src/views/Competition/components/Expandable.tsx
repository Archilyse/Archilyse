import React, { MouseEvent } from 'react';
import { Icon } from 'archilyse-ui-components';
import './expandable.scss';

type ExpandableContext = {
  expandedCategories?: string[];
  onExpand: (key: string[]) => void;
};
const context = React.createContext<ExpandableContext>({ expandedCategories: [], onExpand: () => null });

type Props = {
  id?: string;
  expanded: boolean;
  onExpand: (isClosing: boolean) => void;
  icons?: React.ReactNode[];
};

const Expandable = ({
  expanded,
  onExpand,
  icons = [],
  id = null,
  children,
}: React.PropsWithChildren<Props>): JSX.Element => {
  const handleClick = (event: MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();

    onExpand(expanded);
  };

  const buttonIcon = expanded ? <Icon>arrow_up</Icon> : <Icon>arrow_down</Icon>;
  const ariaLabel = expanded ? 'roll-down' : 'expand';
  const hasAnyIcon = onExpand || icons.length > 0;

  return (
    <div className="expandable-field">
      {children}

      {hasAnyIcon && (
        <div className="icons-container">
          {icons.map((icon, index) => (
            <span key={index}>{icon}</span>
          ))}
          {onExpand && (
            <span id={id}>
              <button onClick={handleClick} aria-label={ariaLabel}>
                {buttonIcon}
              </button>
            </span>
          )}
        </div>
      )}
    </div>
  );
};

Expandable.Provider = context.Provider;
Expandable.Context = context;

export default Expandable;
