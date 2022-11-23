import { useHistory, useLocation, useParams } from 'react-router-dom';
import queryString from 'query-string';
// This will be a wrapper from react rotuer dom to return the same format as before
// As per: https://reactrouter.com/web/example/query-parameters
const useRouter = (): any => {
  const { search, pathname } = useLocation();
  const params = useParams();
  const history = useHistory();
  const query = queryString.parse(search);
  const fullPath = `${pathname}${search}`;
  return {
    pathname,
    query,
    fullPath,
    params,
    history,
    search: search.slice(1), // Strip the `?`
  };
};

export default useRouter;
