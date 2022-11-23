import { CopyPaste } from '../class/export';
import {
  BEGIN_COPY_PASTE_SELECTION,
  BEGIN_DRAGGING_COPY_PASTE_SELECTION,
  BEGIN_ROTATING_COPY_PASTE_SELECTION,
  END_COPY_PASTE_SELECTION,
  END_DRAGGING_COPY_PASTE_SELECTION,
  END_ROTATING_COPY_PASTE_SELECTION,
  RESTORE_COPY_PASTE_FROM_ANOTHER_PLAN,
  SAVE_COPY_PASTE_SELECTION,
  UPDATE_COPY_PASTE_SELECTION,
  UPDATE_DRAGGING_COPY_PASTE_SELECTION,
  UPDATE_ROTATING_COPY_PASTE_SELECTION,
} from '../constants';

export default (state, action) => {
  switch (action.type) {
    case BEGIN_COPY_PASTE_SELECTION:
      return CopyPaste.beginCopyPasteSelection(state, action).updatedState;
    case UPDATE_COPY_PASTE_SELECTION:
      return CopyPaste.updateCopyPasteSelection(state, action).updatedState;

    case END_COPY_PASTE_SELECTION:
      return CopyPaste.endCopyPasteSelection(state, action).updatedState;

    case BEGIN_DRAGGING_COPY_PASTE_SELECTION:
      return CopyPaste.beginDraggingCopyPasteSelection(state, action).updatedState;
    case UPDATE_DRAGGING_COPY_PASTE_SELECTION:
      return CopyPaste.updateDraggingCopyPasteSelection(state, action).updatedState;

    case END_DRAGGING_COPY_PASTE_SELECTION:
      return CopyPaste.endDraggingCopyPasteSelection(state, action).updatedState;

    case SAVE_COPY_PASTE_SELECTION:
      return CopyPaste.saveCopyPasteSelection(state, action).updatedState;
    case RESTORE_COPY_PASTE_FROM_ANOTHER_PLAN:
      return CopyPaste.restoreCopyPasteFromAnotherPlan(state, action).updatedState;

    case BEGIN_ROTATING_COPY_PASTE_SELECTION:
      return CopyPaste.beginRotatingCopyPasteSelection(state, action).updatedState;
    case UPDATE_ROTATING_COPY_PASTE_SELECTION:
      return CopyPaste.updateRotatingCopyPasteSelection(state, action).updatedState;
    case END_ROTATING_COPY_PASTE_SELECTION:
      return CopyPaste.endRotatingCopyPasteSelection(state, action).updatedState;
    default:
      return state;
  }
};
