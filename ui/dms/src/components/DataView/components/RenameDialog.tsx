import React from 'react';
import { Button, Dialog, DialogActions, DialogContent, TextField } from '@material-ui/core';
import './renameDialog.scss';

type RenameDialogProps = {
  open: boolean;
  name: string;
  label: string;
  onClose: () => void;
  onRename: (newName: string) => void;
};

export default function RenameDialog({ open, label, name, onClose, onRename }: RenameDialogProps): JSX.Element {
  const inputRef = React.createRef<HTMLInputElement>();

  const handleButtonRename = React.useCallback(() => {
    const newName = inputRef.current.value;
    onRename(newName);
  }, [onRename, inputRef]);

  const handleTextFieldKeyPress = React.useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        handleButtonRename();
      }
    },
    [handleButtonRename]
  );

  return (
    <Dialog open={open} onClose={onClose} data-testid="rename-dialog" aria-labelledby="form-dialog-title">
      <DialogContent>
        <TextField
          inputRef={inputRef}
          autoFocus
          defaultValue={name}
          onKeyPress={handleTextFieldKeyPress}
          className="rename-dialog-input"
          margin="dense"
          id="name"
          label={label}
          type="text"
          fullWidth
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="primary">
          Cancel
        </Button>
        <Button onClick={handleButtonRename} color="primary">
          Accept
        </Button>
      </DialogActions>
    </Dialog>
  );
}
