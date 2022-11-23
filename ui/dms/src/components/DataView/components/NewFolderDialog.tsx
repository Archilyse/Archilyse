import React from 'react';
import { Button, Dialog, DialogActions, DialogContent, TextField } from '@material-ui/core/';
import './newFolderDialog.scss';

type NewFolderDialogProps = {
  open: boolean;
  onClose: () => void;
  onAccept: (newFolderName: string) => void;
};

export default function NewFolderDialog({ open, onClose, onAccept }: NewFolderDialogProps): JSX.Element {
  const inputRef = React.createRef<HTMLInputElement>();

  const handleButtonAccept = React.useCallback(() => {
    const newFolderName = inputRef.current.value;
    if (newFolderName) {
      onAccept(newFolderName);
    }
  }, [onAccept, inputRef]);

  const handleTextFieldKeyPress = React.useCallback(
    e => {
      if (e.charCode === 13) {
        handleButtonAccept();
      }
    },
    [handleButtonAccept]
  );

  return (
    <Dialog open={open} onClose={onClose} data-testid="new-folder-dialog" aria-labelledby="form-dialog-title">
      <DialogContent>
        <TextField
          inputRef={inputRef}
          autoFocus
          onKeyPress={handleTextFieldKeyPress}
          className="new-folder-dialog-input"
          margin="dense"
          id="name"
          label="Folder name"
          type="text"
          fullWidth
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="primary">
          Cancel
        </Button>
        <Button onClick={handleButtonAccept} color="primary">
          Accept
        </Button>
      </DialogActions>
    </Dialog>
  );
}
