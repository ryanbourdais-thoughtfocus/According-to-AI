import React from 'react';

const StatusMessage = ({ message }) => {
  if (!message) return null;

  return (
    <div
      style={{
        marginTop: "20px",
        padding: "10px",
        borderRadius: "5px",
        textAlign: "center",
        backgroundColor: message.startsWith('Error') ? "#f8d7da" : "#d4edda",
        color: message.startsWith('Error') ? "#721c24" : "#155724",
      }}
    >
      {message}
    </div>
  );
};

export default StatusMessage;
