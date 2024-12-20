# According-to-AI

This project consists of a Flask-based UI and an Azure Functions-based API for audio transcription using OpenAI's Whisper model. The API processes audio files, transcribes speech to text, and the UI provides a user-friendly interface for uploading files and viewing results.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Project](#running-the-project)
- [Testing the API](#testing-the-api)
- [Notes](#notes)

---

## Prerequisites

Before running the project, ensure you have the following installed:

1. **Python 3.8+**: Download from [python.org](https://www.python.org/downloads/).
2. **Azure Functions Core Tools**: For running Azure Functions locally. [Installation Guide](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local#v2).
3. **FFmpeg**: For audio processing. [Download FFmpeg](https://ffmpeg.org/download.html).
4. **CUDA (Optional for GPU Acceleration)**: [NVIDIA’s official site](https://developer.nvidia.com/cuda-downloads).

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/ryanbourdais-thoughtfocus/According-to-AI.git
   cd According-to-AI
   ```

2. **Set Up a Python Virtual Environment**:
   ```bash
   python -m venv .venv
   ```

3. **Activate the Virtual Environment**:
   - **Windows**:
     ```bash
     .venv\Scripts\activate
     ```
   - **macOS/Linux**:
     ```bash
     source .venv/bin/activate
     ```

4. **Install Required Packages**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Install PyTorch with CUDA (if using GPU)**:
   - Visit the [PyTorch website](https://pytorch.org/get-started/locally/) for the correct installation command based on your CUDA version.

## Configuration

1. **Environment Variables**: Create a `.env` file in the root directory and add:
   ```plaintext
   OPENAI_API_KEY=your_openai_api_key
   SPEECH_KEY=your_azure_speech_service_key
   SERVICE_REGION=your_service_region
   ```

2. **FFmpeg Configuration**: Ensure `ffmpeg` is added to your system's PATH.

## Running the Project

### Running the Flask UI

1. **Set Environment Variables**:
   - **Windows Command Prompt**:
     ```bash
     set FLASK_APP=app.py
     set FLASK_ENV=development
     set FLASK_DEBUG=1
     ```
   - **PowerShell**:
     ```bash
     $env:FLASK_APP = "app.py"
     $env:FLASK_ENV = "development"
     $env:FLASK_DEBUG = "1"
     ```
   - **macOS/Linux**:
     ```bash
     export FLASK_APP=app.py
     export FLASK_ENV=development
     export FLASK_DEBUG=1
     ```

2. **Run the Flask Application**:
   ```bash
   flask run
   ```

### Running the Azure Functions API

1. **Start Azure Functions Locally**:
   ```bash
   func start
   ```

2. **Access the API**:
   - The API will be available at: `http://localhost:7071/api/process_file_api`

### Running Both UI and API Simultaneously in VS Code

1. **Open Visual Studio Code** and ensure your workspace is set to the project directory.
2. **Configure Debugging**:
   - Ensure your `.vscode/launch.json` includes a compound configuration to start both the Flask UI and Azure Functions API.
3. **Start Debugging**:
   - Open the command palette in VS Code (Ctrl+Shift+P or Cmd+Shift+P on macOS).
   - Type "Debug: Select and Start Debugging" and select "Start UI and API".
   - After this point, pressing `F5` should start both services in separate terminals.

## Testing the API

You can use tools like [Postman](https://www.postman.com/) or `curl` to test the API.

### Example `curl` Request:

```bash
curl -X POST -F "file=@path_to_your_video_file.mp4" http://localhost:7071/api/process_file_api
```

### Using Postman:
1. Create a new `POST` request.
2. Set the URL to: `http://localhost:7071/api/process_file_api`.
3. In the `Body` section, select `form-data` and add a key named `file` with the video file as the value.
4. Send the request to see the transcription results.

## Notes

- **GPU Acceleration**: Using CUDA can significantly speed up transcription.
- **Audio Processing**: Ensure FFmpeg is installed and accessible.
- **Whisper Model**: The model can be changed based on performance needs.

Feel free to reach out if you encounter any issues or have questions!