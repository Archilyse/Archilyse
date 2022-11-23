import { renderHook } from '@testing-library/react-hooks';
import { MOCK_AUTHENTICATION } from '../../../tests/utils';
import { useHierarchy } from '.';

jest.mock('react-router-dom', () => ({
  useLocation() {
    return {
      pathname: '/units',
      search: '?floor_id=12300',
      hash: '',
      key: 'c6t6fp',
    };
  },
  useParams() {
    return jest.fn();
  },
  useHistory() {
    return jest.fn();
  },
  Link() {
    return jest.fn();
  },
}));

it('Should display a hierarchy of entities from units for admin', async () => {
  MOCK_AUTHENTICATION();

  const { result, waitForNextUpdate } = renderHook(() => useHierarchy());
  await waitForNextUpdate();
  expect(result.current).toMatchSnapshot();
});
