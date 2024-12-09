import React, { useState } from 'react';
import MeetingForm from './components/MeetingForm';
import StatusMessage from './components/StatusMessage';

const App = () => {
  const [status, setStatus] = useState('');

  const handleJoinMeeting = (link) => {
    // Check if the link is valid for Google Meet or Microsoft Teams
    const isGoogleMeet = link.includes('https://meet.google.com/');
    const isMicrosoftTeams = link.includes('https://teams.microsoft.com/');

    if (isGoogleMeet || isMicrosoftTeams) {
      // Set success message for valid links
      setStatus('Bot has successfully joined the meeting.');

      // Clear the status message after 5 seconds
      setTimeout(() => {
        setStatus('');
      }, 5000);
    } else {
      // Clear the success message for invalid links
      setStatus('');
    }
  };

  return (
    <div
      style={{
        position: "relative",
        minHeight: "100vh",
        overflow: "hidden",
      }}
    >
      {/* Background Image */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          backgroundImage: "url('/images/background.jpg')",
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
          filter: "opacity(0.9)", // Adjust the transparency of the image
          zIndex: 0,
        }}
      ></div>

      {/* Content */}
      <div
        className="container"
        style={{
          position: "relative", // Ensure content is above the background
          zIndex: 2,
          backgroundColor: "rgba(255, 255, 255, 1.0)", // Fully opaque white
          borderRadius: "10px",
          padding: "40px",
          maxWidth: "600px",
          margin: "100px auto",
          boxShadow: "0px 4px 10px rgba(0, 0, 0, 0.25)",
          textAlign: "center",
        }}
      >
        <h1 style={{ fontSize: "2.5rem", fontWeight: "bold", color: "#333" }}>
          Meeting Bot
        </h1>
        <p style={{ fontSize: "1.2rem", color: "#555", marginBottom: "20px" }}>
          Paste your meeting link below to let the bot join the meeting.
        </p>
        <MeetingForm onSubmit={handleJoinMeeting} />
        {status && <StatusMessage message={status} />}
      </div>
    </div>
  );
};

export default App;
