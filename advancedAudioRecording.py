import os
import threading
import queue
import time
import base64
import sounddevice as sd
import soundfile as sf
import numpy as np
import pyvirtualaudio
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

class GoogleMeetBot:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.join_status_queue = queue.Queue()
        self.exit_event = threading.Event()
        self.driver = None
        self.meeting_thread = None
        self.audio_queue = queue.Queue()
        self.virtual_audio_device = None
        self.recording_thread = None
        self.driver = None

    def setup_driver(self):
        """
        Setup headless Firefox driver optimized for AWS/cloud environments
        """
        firefox_options = Options()
        firefox_options.add_argument("--headless")  # Explicitly run in headless mode
        firefox_options.add_argument("--no-sandbox")
        firefox_options.add_argument("--disable-dev-shm-usage")
        firefox_options.set_preference("permissions.default.microphone", 2)
        firefox_options.set_preference("permissions.default.camera", 2)
        firefox_options.set_preference("media.navigator.permission.disabled", True)
                
        self.driver = webdriver.Firefox(
            service=Service(),
            options=firefox_options,
        )

    def login_google_account(self):
        """
        Login to Google account
        """
        self.driver.get("https://accounts.google.com/signin")

        try:
            # Wait and enter email
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "identifierId"))
            )
            email_field.send_keys(self.email)
            email_field.send_keys(Keys.RETURN)
            time.sleep(5)

            # Enter password
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "Passwd"))
            )
            
            password_field.send_keys(self.password)
            password_field.send_keys(Keys.RETURN)

            # Wait for login completion
            WebDriverWait(self.driver, 10).until(
                EC.url_contains("myaccount.google.com")
            )
            print("Login successful!")

        except Exception as e:
            print(f"Login failed: {e}")

    def setup_virtual_audio_device(self):
        
        try:
            # Create a virtual audio device
            self.virtual_audio_device = pyvirtualaudio.VirtualAudioDevice()
            
            # Configure the virtual device
            self.virtual_audio_device.set_sample_rate(44100)  # Standard sample rate
            self.virtual_audio_device.set_channels(2)  # Stereo
            
            print("Virtual audio device created successfully.")
            return True
        except Exception as e:
            print(f"Failed to create virtual audio device: {e}")
            return False

    def audio_capture_thread(self, duration=None):
        """
        Capture audio from the virtual audio device
        """
        try:
            # Ensure Recordings directory exists
            os.makedirs("./Recordings", exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"./Recordings/{self.email}_meeting_audio_{timestamp}.wav"
            
            # Start recording
            with sf.SoundFile(filename, mode='w', samplerate=44100, channels=2) as file:
                # Capture audio until signaled to stop
                while not self.exit_event.is_set():
                    # Read audio from virtual device
                    audio_chunk = self.virtual_audio_device.read()
                    
                    if audio_chunk is not None:
                        # Write chunk to file
                        file.write(audio_chunk)
            
            print(f"Audio saved to {filename}")
            return filename
        
        except Exception as e:
            print(f"Error in audio capture: {e}")
            return None

    def modify_audio_capture_script(self):
        """
        Modify browser-side script to route audio to virtual device
        """
        audio_capture_script = """
        class AudioRouting {
            constructor() {
                this.audioContext = new AudioContext();
                this.destination = null;
            }

            async setupAudioRouting() {
                try {
                    // Get browser audio stream
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    const source = this.audioContext.createMediaStreamSource(stream);
                    
                    // Create a destination to send audio to virtual device
                    this.destination = this.audioContext.createMediaStreamDestination();
                    
                    // Connect source to destination
                    source.connect(this.destination);
                    
                    // Expose the stream for potential virtual device routing
                    window.virtualAudioStream = this.destination.stream;
                    
                    console.log('Audio routing setup complete');
                } catch (error) {
                    console.error('Audio routing error:', error);
                }
            }
        }

        // Initialize and setup audio routing
        window.audioRouting = new AudioRouting();
        window.audioRouting.setupAudioRouting();
        """
        return audio_capture_script

    def join_meeting(self, meeting_link):
        """
        Enhanced meeting join method with virtual audio routing
        """
        try:
            # Setup virtual audio device first
            if not self.setup_virtual_audio_device():
                raise Exception("Failed to setup virtual audio device")

            # Existing login and meeting join process
            self.login_google_account()
            self.driver.get(meeting_link)

            # Wait for meeting page
            time.sleep(10)

            # Find and click join button
            join_button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[jsname='Qx7uuf']"))
            )
            join_button.click()

            # Inject modified audio routing script
            self.driver.execute_script(self.modify_audio_capture_script())

            # Start audio recording thread
            self.recording_thread = threading.Thread(target=self.audio_capture_thread)
            self.recording_thread.start()

            # Signal successful join
            self.join_status_queue.put("Bot joined successfully")

            # Keep thread alive until exit
            while not self.exit_event.is_set():
                time.sleep(1)

        except Exception as e:
            print(f"Failed to join the meeting: {e}")
            self.join_status_queue.put(f"Failed to join the meeting: {e}")

    def exit_meeting(self):
        """
        Enhanced exit method to stop audio capture
        """
        try:
            # Set exit event to stop recording
            self.exit_event.set()

            # Wait for recording thread to finish
            if self.recording_thread:
                self.recording_thread.join()

            # Close virtual audio device
            if self.virtual_audio_device:
                self.virtual_audio_device.close()

            # Existing exit meeting logic
            leave_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Leave call']"))
            )
            leave_button.click()

            print("Left the meeting successfully!")
        
        except Exception as e:
            print(f"Error during meeting exit: {e}")
        finally:
            # Close browser
            if self.driver:
                self.driver.quit()

    def run_bot(self, meeting_link):
        """
        Run bot in a separate thread
        """
        self.meeting_thread = threading.Thread(target=self.join_meeting, args=(meeting_link,))
        self.meeting_thread.start()

        join_status = self.join_status_queue.get()
        return join_status

