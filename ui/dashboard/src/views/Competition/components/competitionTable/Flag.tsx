import React from 'react';
import { Icon } from 'archilyse-ui-components';
import { C } from '../../../../common';
import { isFirefox } from '../../../../common/modules';
import CompetitionTooltip from '../CompetitionTooltip';

const ICON_STYLE = (color): React.CSSProperties => ({
  fontSize: 18,
  color: color || C.COLORS.GREY,
  marginTop: 0,
  marginLeft: 5,
  position: 'absolute',

  ...(isFirefox() ? { top: '-14px' } : {}), // magic number, have no clue why but it works
});

type Props = {
  title: string;
  color?: string;
};

const Flag = ({ title, color }: Props): JSX.Element => {
  return (
    <CompetitionTooltip title={title}>
      <span className="flag-container">
        <Icon style={ICON_STYLE(color)}>flag</Icon>
      </span>
    </CompetitionTooltip>
  );
};

export default Flag;
