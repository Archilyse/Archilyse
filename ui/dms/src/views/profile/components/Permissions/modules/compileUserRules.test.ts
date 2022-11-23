import { C } from 'Common';
import compileUserRules from './compileUserRules';

const { EDIT, READ } = C.DMS_PERMISSIONS;

const MOCK_CASE_SINGLE = [
  { permission: EDIT, sites: [{ id: 1461, name: 'CustomClient2 B' }] },
  { permission: READ, sites: [{ id: 1467, name: 'test-site' }] },
];

const EXPECTED_COMPILED_SINGLE = [
  { rights: C.DMS_PERMISSIONS.EDIT, site_id: 1461 },
  { rights: C.DMS_PERMISSIONS.READ, site_id: 1467 },
];

const MOCK_CASE_SEVERAL = [
  {
    permission: EDIT,
    sites: [
      { id: 1516, name: 'CustomClient2 B ' },
      { id: 1461, name: 'CustomClient2 B' },
      { id: 1465, name: 'CustomClient2 A' },
    ],
  },
  { permission: READ, sites: [{ id: 1467, name: 'test-site' }] },
];

const EXPECTED_COMPILED_AGGREGATED = [
  { rights: EDIT, site_id: 1516 },
  { rights: EDIT, site_id: 1461 },
  { rights: EDIT, site_id: 1465 },
  { rights: READ, site_id: 1467 },
];

const TEST_CASES = [
  { input: [], expected: [], description: 'Parse empty rules' },
  {
    input: MOCK_CASE_SINGLE,
    expected: EXPECTED_COMPILED_SINGLE,
    description: 'Parse rules with one right and',
  },
  {
    input: MOCK_CASE_SEVERAL,
    expected: EXPECTED_COMPILED_AGGREGATED,
    description: 'Compile rules with one right for several sites into one rule per right & site',
  },
];

describe('compileUserRules function', () => {
  for (const test of TEST_CASES) {
    it(test.description, () => {
      const rules = compileUserRules(test.input);
      expect(rules).toStrictEqual(test.expected);
    });
  }
});
