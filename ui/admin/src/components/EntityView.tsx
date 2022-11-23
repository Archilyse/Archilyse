import React, { useContext, useState } from 'react';
import removeFalsy from 'Common/modules/removeFalsy';
import { Form, SnackbarContext } from 'archilyse-ui-components';
import { ProviderRequest } from '../providers';
import { useRouter } from '../common/hooks';
import ConfirmDeleteDialog from './ConfirmDeleteDialog';
import './entityView.scss';

const ENTITIES_WITHOUT_PARENT = ['client', 'user'];
const CREATE = 'Create';
const SAVE = 'Save';
const NO_PARENT_INFO_MESSAGE = 'Missing parent info while trying to create an entity';

const WAIT_TO_GO_BACK_MS = 2000;
const VALIDATION_ERRORS = [400, 422];

const hasFile = data => Object.values(data).some(value => value instanceof File || value instanceof FileList);

const Title = ({ context, entity, newEntity }) => {
  let title;
  if (newEntity) {
    title = `New ${context}`;
  } else if (entity.name) {
    title = `${entity.name}`;
  } else {
    title = `Editing ${context?.toLowerCase()}: ${entity.id}`;
  }
  return (
    <div className="title">
      <h3>{title}</h3>
    </div>
  );
};

const submitForm = async (onSubmitFn, data, id) => {
  try {
    await onSubmitFn(data, id);
  } catch (error) {
    console.log('Error submitting a form in an entity', error);
    if (error.response && !VALIDATION_ERRORS.includes(error.response.status)) {
      throw error;
    }
  }
};

const EntityView = ({
  entity,
  fields,
  context,
  parent = undefined,
  disableDelete = false,
  parentKey = '',
  onCreate = undefined,
  onUpdate = undefined,
  onSubmit = undefined,
  onSubmitDelete = undefined,
  onChange = undefined,
}) => {
  const [open, setDialogStatus] = useState(false);
  const [buttonDisabledStatus, setDisableFormButton] = useState(false);
  const router = useRouter();

  const snackbar = useContext(SnackbarContext);

  const newEntity = Boolean(parent);

  const toggleDialog = () => setDialogStatus(!open);

  const onUpdateDefault = async data => {
    removeFalsy(data);
    if (context === 'plan') await ProviderRequest.put(`${context}/${entity.id}/floors`, data);
    else await ProviderRequest.put(`${context}/${entity.id}`, data);

    if (onSubmit) await submitForm(onSubmit, data, entity.id);
    snackbar.show({ message: 'Updated successfully', severity: 'success' });
  };

  const onCreateDefault = async data => {
    setDisableFormButton(true);
    removeFalsy(data);
    data[parentKey] = parent.id;
    const method = hasFile(data) ? 'multipart' : 'post';
    // disable the form button while the request is made
    try {
      const newEntity = await ProviderRequest[method](`${context}/`, data);
      if (onSubmit) await submitForm(onSubmit, data, newEntity?.id);
      snackbar.show({ message: 'Created successfully', severity: 'success' });
      setDisableFormButton(false);
    } catch (error) {
      setDisableFormButton(false);
    }
  };

  const onDelete = async () => {
    snackbar.show({ message: 'Deleting...', severity: 'info' });
    await ProviderRequest.delete(`${context}/${entity.id}`);
    toggleDialog();
    snackbar.show({ message: 'Deleted successfully', severity: 'success' });
    onSubmitDelete ? onSubmitDelete() : setTimeout(() => router.history.goBack(), WAIT_TO_GO_BACK_MS);
  };

  const DeleteButton = props => {
    if (newEntity || disableDelete) return null;
    return (
      <div className="delete-button">
        <button className="secondary-button" onClick={toggleDialog}>
          Delete
        </button>
      </div>
    );
  };

  if (
    newEntity &&
    !router.query[parentKey] &&
    !parent[parentKey.split('_')[1]] &&
    !ENTITIES_WITHOUT_PARENT.includes(context)
  ) {
    snackbar.show({ message: NO_PARENT_INFO_MESSAGE, severity: 'error' });

    return null;
  }

  const onSubmitForm = newEntity ? (onCreate ? onCreate : onCreateDefault) : onUpdate ? onUpdate : onUpdateDefault;
  const submitText = newEntity ? CREATE : SAVE;

  return (
    <>
      <div>
        <Title entity={entity} context={context} newEntity={newEntity} />
        <Form
          fields={fields}
          value={{ ...entity }}
          onSubmit={onSubmitForm}
          onChange={onChange}
          submitText={submitText}
          buttonDisabledStatus={buttonDisabledStatus}
        />
        <DeleteButton />
      </div>
      <ConfirmDeleteDialog open={open} onCancel={toggleDialog} onAccept={onDelete} />
    </>
  );
};

export default EntityView;
