import { Icon } from 'archilyse-ui-components';
import { Modal } from '@material-ui/core';
import C from 'Common/constants';
import React, { useState } from 'react';

const ICON_STYLE = {
  fontSize: 40,
  marginLeft: 0,
};

type Props = {
  children: (options: { onClose: () => void }) => React.ReactElement;
};

const OpenHeatmapsModalButton = ({ children }: Props) => {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button data-testid="open-heatmap-modal" onClick={() => setOpen(true)} className="open-heatmaps-modal-button">
        <Icon style={ICON_STYLE}>aspect_ratio</Icon>
      </button>
      <Modal
        aria-labelledby="environmental-modal"
        aria-describedby="environmental-modal"
        open={open}
        onClose={() => setOpen(false)}
        style={C.CSS.MODAL_STYLE}
      >
        {children({ onClose: () => setOpen(false) })}
      </Modal>
    </>
  );
};

export default OpenHeatmapsModalButton;
