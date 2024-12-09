import React, { useState } from 'react';

const MeetingForm = ({ onSubmit }) => {
  const [meetingLink, setMeetingLink] = useState('');
  const [error, setError] = useState(''); // State for error message

  const handleSubmit = (e) => {
    e.preventDefault();

    // Validation Logic: Allow only Google Meet or Microsoft Teams links
    const isGoogleMeet = meetingLink.includes('https://meet.google.com/');
    const isMicrosoftTeams = meetingLink.includes('https://teams.microsoft.com/');

    if (!isGoogleMeet && !isMicrosoftTeams) {
      setError('Only Google Meet or Microsoft Teams links are allowed.');
      return; // Prevent form submission
    }

    // If valid, submit the link and reset the input field
    setError(''); // Clear any previous errors
    onSubmit(meetingLink); // Call the parent function
    setMeetingLink(''); // Clear the input field after submission

    // Clear the form after 5 seconds
    setTimeout(() => {
      setMeetingLink('');
      setError('');
    }, 5000);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="mb-3">
        <input
          type="url"
          className="form-control"
          placeholder="Paste your meeting link (Google Meet or Teams)"
          value={meetingLink}
          onChange={(e) => setMeetingLink(e.target.value)}
          required
        />
      </div>
      {/* Display error message */}
      {error && (
        <div
          style={{
            color: 'red',
            fontWeight: 'bold',
            marginBottom: '15px',
            fontSize: '14px',
          }}
        >
          {error}
        </div>
      )}
      <button type="submit" className="btn btn-primary btn-block">
        Join Meeting
      </button>
    </form>
  );
};

export default MeetingForm;
