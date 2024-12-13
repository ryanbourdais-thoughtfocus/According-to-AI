import os
import threading
import wave
import pyaudio
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.firefox import GeckoDriverManager
import time
import queue

class GoogleMeetBot:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.recording = False
        self.join_status_queue = queue.Queue()
        self.exit_event = threading.Event()
        self.driver = None
        self.audio_thread = None
        self.meeting_thread = None
        self.setup_driver()

    def __del__(self):
        self.exit_meeting()

    def setup_driver(self):
        firefox_options = Options()
        firefox_options.add_argument("--headless")
        firefox_options.add_argument("--start-maximized")
        firefox_options.add_argument("--mute-audio")
        firefox_options.set_preference("permissions.default.microphone", 2)
        firefox_options.set_preference("permissions.default.camera", 2)

        self.driver = webdriver.Firefox(
            service=Service(GeckoDriverManager().install()),
            options=firefox_options,
        )

    def setup_audio_rerouting(self):
        """Setup the audio rerouting using VB-CABLE."""
        print("Ensuring VB-CABLE is set as the default audio device.")
        # In Windows, VB-CABLE needs to be set as the default playback device manually.
        # Ensure this is done before running the bot.

    def record_audio(self, output_file="meeting_audio.wav"):
        """Record VB-CABLE output using PyAudio."""
        self.recording = True
        audio = pyaudio.PyAudio()

        # Find the VB-CABLE "CABLE Output" device
        cable_output_device_index = None
        for i in range(audio.get_device_count()):
            device_info = audio.get_device_info_by_index(i)
            if "CABLE Output" in device_info.get("name", ""):
                cable_output_device_index = i
                break

        if cable_output_device_index is None:
            raise Exception("VB-CABLE 'CABLE Output' device not found. Ensure VB-CABLE is installed and configured.")

        print(f"Using VB-CABLE device: {cable_output_device_index} - {device_info['name']}")

        stream = audio.open(
            format=pyaudio.paInt16,
            channels=2,
            rate=44100,
            input=True,
            input_device_index=cable_output_device_index,
            frames_per_buffer=1024,
        )

        frames = []

        print("Recording audio...")
        while self.recording and not self.exit_event.is_set():
            data = stream.read(1024, exception_on_overflow=False)
            frames.append(data)

        print("Stopping audio recording...")
        stream.stop_stream()
        stream.close()
        audio.terminate()

        os.makedirs("./Recordings", exist_ok=True)
        file_path = f"./Recordings/{output_file}"

        with wave.open(file_path, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(44100)
            wf.writeframes(b"".join(frames))
        print(f"Audio saved to {file_path}")

    def login_google_account(self):
        self.driver.get("https://accounts.google.com/signin")

        try:
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "identifierId"))
            )
            email_field.send_keys(self.email)
            email_field.send_keys(Keys.RETURN)
            time.sleep(5)

            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "Passwd"))
            )

            password_field.send_keys(self.password)
            password_field.send_keys(Keys.RETURN)

            WebDriverWait(self.driver, 10).until(
                EC.url_contains("myaccount.google.com")
            )
            print("Login successful!")

        except Exception as e:
            print(f"Login failed: {e}")
            self.driver.quit()

    def exit_meeting(self):
        try:
            self.exit_event.set()
            self.recording = False

            if self.audio_thread and self.audio_thread.is_alive():
                self.audio_thread.join(timeout=5)

            try:
                leave_button = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Leave call']"))
                )
                leave_button.click()
                print("Left the meeting successfully!")
            except Exception as leave_e:
                print(f"Could not find leave button: {leave_e}")

            self.logout()
            print("Meeting exit process completed.")
        except Exception as e:
            print(f"Error during meeting exit: {e}")
        finally:
            if self.driver:
                self.driver.quit()

    def join_meeting(self, meeting_link):
        try:
            self.login_google_account()
            self.driver.get(meeting_link)

            print("Waiting for the meeting page to load...")
            time.sleep(10)

            join_button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[jsname='Qx7uuf']"))
            )
            join_button.click()
            print("Joined the meeting successfully!")

            self.join_status_queue.put("Bot joined successfully")

            self.audio_thread = threading.Thread(target=self.record_audio, args=("meeting_audio.wav",))
            self.audio_thread.start()

            print("Bot is now in the meeting.")

            while not self.exit_event.is_set():
                time.sleep(1)

        except Exception as e:
            print(f"Failed to join the meeting: {e}")
            self.join_status_queue.put(f"Failed to join the meeting: {e}")
            self.recording = False
            if self.driver:
                self.driver.quit()

    def logout(self):
        try:
            self.driver.get("https://accounts.google.com/Logout")
            print("Logged out successfully!")
        except Exception as e:
            print(f"Logout failed: {e}")

    def run_bot(self, meeting_link):
        self.setup_audio_rerouting()
        self.meeting_thread = threading.Thread(target=self.join_meeting, args=(meeting_link,))
        self.meeting_thread.start()

        join_status = self.join_status_queue.get()
        return join_status
