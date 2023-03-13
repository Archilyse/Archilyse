import React, { useContext } from 'react';
import useSWR from 'swr';
import { Form, SnackbarContext } from 'archilyse-ui-components';
import { SiteModel } from 'Common/types';
import formFields from '../../common/forms/copySite';
import { useRouter } from '../../common/hooks';
import { ProviderRequest } from '../../providers';
import { C } from '../../common';

const getValue = (site: SiteModel) => {
  return {
    name: site?.name || '',
    client_site_id: site?.client_site_id || '',
    client_id: site.client_id || '',
  };
};

const SiteCopy = () => {
  const { params } = useRouter();
  const { data: site } = useSWR(C.ENDPOINTS.SITE_BY_ID(params.id), ProviderRequest.get);
  const { data: clients } = useSWR(C.ENDPOINTS.CLIENT(), ProviderRequest.get);

  const snackbar = useContext(SnackbarContext);

  const onSubmitForm = async data => {
    await ProviderRequest.post(`site/${site.id}/copy`, data);
    snackbar.show({ message: 'Copied succesfully', severity: 'success' });
  };

  if (!site || !clients) return null;

  formFields.map(field => {
    if (field.name === 'client_target_id') {
      field.options = clients.map(client => ({ label: client.name, value: client.id }));
    }
    return field;
  });

  return (
    <>
      <div>
        <div className="title">
          <h3>Copy site</h3>
        </div>
        <Form fields={formFields} value={getValue(site)} onSubmit={onSubmitForm} submitText={'Copy site'} />
      </div>
    </>
  );
};

export default SiteCopy;
