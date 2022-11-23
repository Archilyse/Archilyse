import React from 'react';
import { ProviderRequest } from '../providers';

const FileUploadRenderer = args => {
  async function uploadFile(event) {
    const formData = new FormData();
    formData.append(args.name, event.target.files[0]);
    try {
      const response = await ProviderRequest.post(args.url, formData);
      args.onSuccess(response);
    } catch (error) {
      args.onError(error);
    }
  }

  return <input id={args.id} onChange={uploadFile} type="file" />;
};

export default FileUploadRenderer;
