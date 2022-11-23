import React, { FunctionComponent } from 'react';
import { Icon as MUIIcon } from '@material-ui/core';
import C from '../../constants';
import logo from '../../img/svg/logo';
import dots from '../../img/svg/dots';
import sun from '../../img/svg/sun';
import arrow_up from '../../img/svg/arrow_up';
import arrow_down from '../../img/svg/arrow_down';
import add from '../../img/svg/add';
import plus from '../../img/svg/plus';
import fslash from '../../img/svg/fslash';
import cut from '../../img/svg/Cut';
import paste from '../../img/svg/Paste';
import robot from '../../img/svg/robot';

const customIcons = {
  logo,
  sun,
  dots,
  arrow_up,
  arrow_down,
  add,
  plus,
  fslash,
  cut,
  paste,
  robot,
} as const;

type IconProps = {
  children: string;
  style?: React.CSSProperties;
  className?: string;
};

const Icon: FunctionComponent<IconProps> = ({ children, style = {}, ...props }: IconProps) => {
  const CustomIcon = customIcons[children];

  if (CustomIcon) return <CustomIcon fill={C.COLORS.ICONS_GREY} style={style} {...props} />;

  return (
    <MUIIcon style={{ fontSize: '24px', color: C.COLORS.ICONS_GREY, marginLeft: '5px', ...style }} {...props}>
      {children}
    </MUIIcon>
  );
};

export default Icon;
