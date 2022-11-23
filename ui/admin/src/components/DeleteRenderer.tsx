import React from 'react';

const DeleteRenderer = ({ onClick }) => {
  return (
    <div onClick={onClick}>
      <a href="#">Delete</a>
    </div>
  );
};

export default DeleteRenderer;
