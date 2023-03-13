import { C } from 'Common';
import { getColumns } from './Sites';

const { ADMIN, TEAMMEMBER } = C.ROLES;

const REGULAR_COLUMNS = [
  'id',
  'name',
  'client_site_id',
  'region',
  'ready',
  'pipeline_and_qa_complete',
  'qa_link',
  'full_slam_results',
  'heatmaps_qa_complete',
  'pipelines',
];
const ADMIN_COLUMNS = [
  'classification_scheme',
  'simulations',
  'zip',
  'group',
  'delivered',
  'p_hubble',
  'actions',
  'copy_site',
  'surroundings',
];
describe('getColumns', () => {
  it(`As an ${ADMIN}, I get all columns`, () => {
    const columns = getColumns({}, [ADMIN]).map(c => c.field);
    expect(columns).toStrictEqual([...REGULAR_COLUMNS, ...ADMIN_COLUMNS]);
  });

  it(`As a ${TEAMMEMBER}, I get regular columns & "action" column`, () => {
    const columns = getColumns({}, [TEAMMEMBER]).map(c => c.field);
    expect(columns).toStrictEqual([...REGULAR_COLUMNS, 'actions']);
  });

  it(`As a non ${ADMIN} nor ${TEAMMEMBER} I get only regular columns`, () => {
    const columns = getColumns({}, []).map(c => c.field);
    expect(columns).toStrictEqual(REGULAR_COLUMNS);
  });
});
