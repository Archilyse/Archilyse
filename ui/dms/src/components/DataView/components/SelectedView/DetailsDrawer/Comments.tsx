import React, { useEffect, useRef, useState } from 'react';
import { createMuiTheme, ThemeProvider } from '@material-ui/core/styles';
import { TextField } from '@material-ui/core';
import { DateUtils, Icon } from 'archilyse-ui-components';
import { C } from 'Common';
import './comments.scss';

const commentsTheme = createMuiTheme({
  palette: {
    primary: {
      main: C.COLORS.PRIMARY_COLOR,
    },
  },
});

const AUTHOR_ICON_STYLE = { marginRight: '5px', marginLeft: '0' };

const MAX_COMMENTS_ROWS = 2;

const Comment = ({ comment }) => {
  return (
    <div className="comment">
      <div className="comment-header">
        <p className="comment-author">
          <Icon style={AUTHOR_ICON_STYLE}>person</Icon> {comment?.creator?.name}
        </p>
        <p>{DateUtils.getDateFromISOString(comment.created)}</p>
      </div>
      <p>{comment.comment}</p>
    </div>
  );
};

const Comments = ({ comments, onAddComment }) => {
  const [newComment, setNewComment] = useState('');
  const endComments = useRef(null);

  useEffect(() => {
    if (endComments && endComments.current) {
      endComments.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [endComments, comments]);

  return (
    <div className="comments">
      <ThemeProvider theme={commentsTheme}>
        <div className="current-comments">
          {comments.map(comment => (
            <div key={comment.id} data-testid="comment">
              <Comment comment={comment} />
              <div className="divider" />
            </div>
          ))}
          <div ref={endComments}></div>
        </div>
        <div className="add-comment">
          <TextField
            label="Add a comment & press enter"
            name="add-comment"
            id="add-comment"
            multiline
            rowsMax={MAX_COMMENTS_ROWS}
            value={newComment}
            variant="outlined"
            onChange={event => setNewComment(event.target.value)}
            onKeyPress={ev => {
              // @TODO: Allow shift enter for multiline comments
              if (ev.key === 'Enter') {
                ev.preventDefault();
                if (newComment) {
                  onAddComment(newComment);
                  setNewComment('');
                }
              }
            }}
          />
        </div>
      </ThemeProvider>
    </div>
  );
};

export default Comments;
