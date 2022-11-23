import React from 'react';
import { Button, Dialog, DialogActions, DialogContent, DialogContentText } from '@material-ui/core';
import './confirmDeleteDialog.scss';

const ConfirmDeleteDialog = ({ open, onCancel, onAccept }) => (
  <Dialog
    open={open}
    className={'delete-dialog'}
    onClose={onCancel}
    aria-labelledby="alert-dialog-title"
    aria-describedby="alert-dialog-description"
  >
    <DialogContent>
      <DialogContentText id="alert-dialog-description">
        Are you sure you want to delete this? <b>This action cannot be undone</b>
      </DialogContentText>
      <DialogActions>
        <Button onClick={onCancel} color="primary">
          Cancel
        </Button>
        <Button
          onClick={onAccept}
          className="delete-button button-confirm"
          variant={'contained'}
          color="secondary"
          autoFocus
        >
          Delete
        </Button>
      </DialogActions>
    </DialogContent>
  </Dialog>
);

export default ConfirmDeleteDialog;
