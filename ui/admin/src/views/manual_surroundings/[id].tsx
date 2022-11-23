import React from 'react';
import useSWR from 'swr';
import { useRouter } from '../../common/hooks';
import { ProviderRequest } from '../../providers';
import { C } from '../../common';
import { EditorMap } from './components';

const NOT_FOUND = 404;

const ManualSurroundings = () => {
  const { params } = useRouter();
  const { data: site } = useSWR(C.ENDPOINTS.SITE_BY_ID(params.id, true), ProviderRequest.get);
  const { data: existing_surr, error: surr_error } = useSWR(
    C.ENDPOINTS.MANUAL_SURROUNDINGS(params.id),
    ProviderRequest.get
  );
  const { data: existing_plans, error: georef_plans_error } = useSWR(
    C.ENDPOINTS.SITE_GEOREF_PLANS(params.id),
    ProviderRequest.get
  );

  if (!site || (!existing_surr && !surr_error) || (!existing_plans && !georef_plans_error)) return null;

  if (surr_error && surr_error.response && surr_error.response.status != NOT_FOUND) {
    throw surr_error;
  }
  if (georef_plans_error && georef_plans_error.response && georef_plans_error.response.status != NOT_FOUND) {
    throw georef_plans_error;
  }

  return (
    <EditorMap
      coordinates={[site.lat, site.lon]}
      surrGeoJson={existing_surr?.surroundings}
      sitePlans={existing_plans}
      siteID={params.id}
    />
  );
};

export default ManualSurroundings;
