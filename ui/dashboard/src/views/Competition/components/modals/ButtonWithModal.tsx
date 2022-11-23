import React, { useState } from 'react';
import cn from 'classnames';
import { Modal } from '@material-ui/core';
import { C } from '../../../../common';
import { Can } from '../../../../components';
import './buttonWithModal.scss';

type ChildrenParams = {
  onClose: () => void;
};

type Props = {
  label: React.ReactNode;
  className?: string;
  children: (params: ChildrenParams) => React.ReactElement;
};

const ButtonWithModal = ({ label, className, children }: Props): JSX.Element => {
  const [open, setOpen] = useState(false);

  const handleClose = () => {
    setOpen(false);
  };

  return (
    <Can
      perform="competition:change-weights"
      yes={() => (
        <span className={cn({ 'button-with-modal': !className })}>
          <button onClick={() => setOpen(true)} className={className}>
            {label}
          </button>
          <Modal
            aria-labelledby="environmental-modal"
            aria-describedby="environmental-modal"
            open={open}
            onClose={handleClose}
            style={C.CSS.MODAL_STYLE}
          >
            {children({ onClose: handleClose })}
          </Modal>
        </span>
      )}
    />
  );
};

export default ButtonWithModal;
