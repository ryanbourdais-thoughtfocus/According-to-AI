import axios from 'axios';

export const joinMeeting = async (link) => {
  const apiUrl = 'http://localhost:5000/join-meeting'; // Replace with your backend API URL
  try {
    const response = await axios.post(apiUrl, { link });
    return response.data.message;
  } catch (error) {
    console.error('Error joining meeting:', error);
    throw new Error('Failed to connect to the backend.');
  }
};

