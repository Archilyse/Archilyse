import React from 'react';
import useSWR from 'swr';
import sanitizeQa from 'Common/modules/sanitizeQa';
import { useRouter } from '../../common/hooks';
import { ProviderRequest } from '../../providers';
import { SiteView } from '../../components';
import { C } from '../../common';

const NOT_FOUND = 404;

const Site = () => {
  const { params } = useRouter();
  const { data: site } = useSWR(C.ENDPOINTS.SITE_BY_ID(params.id), ProviderRequest.get);
  const { data: qa, error } = useSWR(C.ENDPOINTS.QA_BY_SITE(params.id), ProviderRequest.get, {
    shouldRetryOnError: false,
  });
  const { data: defaultQaHeaders } = useSWR(C.URLS.QA_TEMPLATE_HEADERS(), ProviderRequest.get);

  if (error && error.response && error.response.status !== NOT_FOUND) {
    throw error;
  }
  if (!site || !qa) return null;
  qa.data = sanitizeQa(qa, defaultQaHeaders);
  return <SiteView site={site} qa={qa} isUpdated={true} />;
};

export default Site;
