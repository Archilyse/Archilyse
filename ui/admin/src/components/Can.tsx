import { ReactNode } from 'react';
import { ActionsType, checkAccess } from '../common/roles';
import { C } from '../common';

const { ROLES } = C;

type Props = {
  role?: typeof ROLES[keyof typeof ROLES];
  perform: ActionsType | ActionsType[];
  yes?: () => ReactNode;
  no?: () => ReactNode;
};

const Can = ({ perform, yes = () => null, no = () => null }: Props) => {
  return checkAccess(perform) ? (yes() as JSX.Element) : (no() as JSX.Element);
};

export default Can;
