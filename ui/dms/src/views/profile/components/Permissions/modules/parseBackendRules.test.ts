import { C } from 'Common';
import parseBackendRules from './parseBackendRules';

const MOCK_SITES = [
  { id: 1467, name: 'test-site' },
  { id: 1516, name: 'CustomClient2 B ' },
  { id: 1461, name: 'CustomClient2 B' },
  { id: 1465, name: 'CustomClient2 A' },
];

const { EDIT, READ } = C.DMS_PERMISSIONS;

const MOCK_CASE_SINGLE = [
  { rights: C.DMS_PERMISSIONS.EDIT, site_id: 1461, user_id: 149 },
  { rights: C.DMS_PERMISSIONS.READ, site_id: 1467, user_id: 149 },
];
const MOCK_CASE_SEVERAL = [
  { rights: EDIT, site_id: 1461, user_id: 149 },
  { rights: READ, site_id: 1467, user_id: 149 },
  { rights: EDIT, site_id: 1516, user_id: 184 },
  { rights: EDIT, site_id: 1461, user_id: 184 },
  { rights: EDIT, site_id: 1465, user_id: 184 },
  { rights: READ, site_id: 1467, user_id: 184 },
];

const EXPECTED_PARSED_SINGLE = {
  '149': [
    { permission: EDIT, sites: [{ id: 1461, name: 'CustomClient2 B' }] },
    { permission: READ, sites: [{ id: 1467, name: 'test-site' }] },
  ],
};

const EXPECTED_PARSED_AGGREGATED = {
  '149': [
    { permission: EDIT, sites: [{ id: 1461, name: 'CustomClient2 B' }] },
    { permission: READ, sites: [{ id: 1467, name: 'test-site' }] },
  ],
  '184': [
    {
      permission: EDIT,
      sites: [
        { id: 1516, name: 'CustomClient2 B ' },
        { id: 1461, name: 'CustomClient2 B' },
        { id: 1465, name: 'CustomClient2 A' },
      ],
    },
    { permission: READ, sites: [{ id: 1467, name: 'test-site' }] },
  ],
};

const TEST_CASES = [
  { input: [], expected: {}, description: 'Parse empty rules' },
  {
    input: MOCK_CASE_SINGLE,
    expected: EXPECTED_PARSED_SINGLE,
    description: 'Parse rules for the same user, one site per right',
  },
  {
    input: MOCK_CASE_SEVERAL,
    expected: EXPECTED_PARSED_AGGREGATED,
    description: 'Parse rules for the several users, aggregating sites that have the same right',
  },
];

describe('parseBackendRules function', () => {
  for (const test of TEST_CASES) {
    it(test.description, () => {
      const rules = parseBackendRules(test.input, MOCK_SITES);
      expect(rules).toStrictEqual(test.expected);
    });
  }
});
