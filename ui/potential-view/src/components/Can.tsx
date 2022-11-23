import { ReactNode } from 'react';
import { ActionsType, checkAccess } from '../common/roles';
import { C } from '../common';

const { ROLES } = C;

export type CanPropsType = {
  role?: typeof ROLES[keyof typeof ROLES];
  perform: ActionsType | ActionsType[];
  yes?: () => ReactNode;
  no?: () => ReactNode;
};

const Can = ({ perform, yes = () => null, no = () => null }: CanPropsType): JSX.Element => {
  return checkAccess(perform) ? (yes() as JSX.Element) : (no() as JSX.Element);
};

export default Can;
