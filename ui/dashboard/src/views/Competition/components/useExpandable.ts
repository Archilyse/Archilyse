import { useContext } from 'react';
import Expandable from './Expandable';
import { checkIsExpanded } from './utils';

const useExpandable = (categoryKey: string) => {
  const { expandedCategories, onExpand } = useContext(Expandable.Context);

  const handleExpand = (isClosing: boolean) => {
    if (isClosing) {
      onExpand(expandedCategories.filter(item => !item.includes(categoryKey)));
    } else {
      onExpand([...expandedCategories, categoryKey]);
    }
  };

  return { expanded: checkIsExpanded(categoryKey, expandedCategories), onExpand: handleExpand };
};

export default useExpandable;
