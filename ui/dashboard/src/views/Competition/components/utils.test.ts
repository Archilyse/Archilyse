import { checkIsExpanded, getSafePercents } from './utils';

it.each([
  ['main', [], false],
  ['main', ['main'], true],
  ['main', ['main', 'main.subsection'], true],
  ['main', ['main', 'main.subsection.item'], true],
  ['main1', ['main', 'main.subsection.item'], false],
  ['maiw', ['main', 'main.subsection.item'], false],
  ['mai', ['main', 'main.subsection.item'], false],
  ['test', ['main', 'main.subsection.item'], false],
  ['main.subsection', ['main', 'main.subsection.item'], true],
  ['main.subsection1', ['main', 'main.subsection.item'], false],
  ['main.subsectiow', ['main', 'main.subsection.item'], false],
  ['main.subsec', ['main', 'main.subsection.item'], false],
  ['main.subsection.item', ['main', 'main.subsection.item'], true],
  ['main.subsection.item1', ['main', 'main.subsection.item'], false],
  ['main.subsection.itew', ['main', 'main.subsection.item'], false],
  ['main.subsection.ite', ['main', 'main.subsection.item'], false],
  ['main.subsection.item.some_more_items', ['main', 'main.subsection.item'], false],
])('checkIsExpanded -> does "%s" exist in %p? %s', (key, selectedCategories, expected) => {
  expect(checkIsExpanded(key, selectedCategories)).toBe(expected);
});

it.each([
  [null, ['—', 0]],
  [undefined, ['—', 0]],
  [0.5, ['50%', 50]],
  [0.3333333334, ['33.3%', 33.3]],
  [1, ['100%', 100]],
  [0, ['0%', 0]],
  [150, ['100%', 100]],
  [-10, ['0%', 0]],
])('getSafePercents -> %s returns %p', (value, expected) => {
  expect(getSafePercents(value)).toEqual(expected);
});
