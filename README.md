# According-to-AI
# Audio Transcription API using Whisper and Azure Functions

This project is an Azure Functions-based API that processes audio files and transcribes speech to text using OpenAI's Whisper model. The API accepts a video file, extracts the audio, and transcribes it, leveraging Whisper and PyTorch for efficient speech recognition.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Project](#running-the-project)
- [Testing the API](#testing-the-api)
- [Notes](#notes)

---

## Prerequisites

Before running the project, make sure you have the following installed:

1. **Python 3.8+**: Python 3.8 or later must be installed on your machine. You can download it from [python.org](https://www.python.org/downloads/).

2. **Azure Functions Core Tools**: This is needed to run Azure Functions locally.
   - **Installation Guide**:
     - **Windows**: Use the MSI installer from [Azure Functions Core Tools](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local#v2).
     - **macOS/Linux**: Follow the installation instructions provided in the [Azure Functions documentation](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local#v2).

3. **FFmpeg**: Required for audio processing.
   - **Installation Guide**:
     - Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html).
     - Follow the instructions for your operating system to add FFmpeg to your system's PATH.

4. **CUDA (Optional for GPU Acceleration)**:
   - If you want to use NVIDIA CUDA for GPU acceleration with PyTorch:
     - Install CUDA from [NVIDIA’s official site](https://developer.nvidia.com/cuda-downloads).
     - Make sure your NVIDIA drivers are up to date.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/your-repo-name.git
   cd your-repo-name
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

4. **Install Requirements**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Install PyTorch with CUDA (if using GPU)**:
   - Visit the [PyTorch website](https://pytorch.org/get-started/locally/) to get the correct installation command based on your CUDA version.
   - Example for CUDA 11.7:
     ```bash
     pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu117
     ```

## Checking Your CUDA Version

Before installing PyTorch with CUDA support, you need to determine the CUDA version that is compatible with your GPU and installed on your system.

### Steps to Check Your CUDA Version:

1. **Check CUDA Version Installed**:
   - Open your command prompt (Windows) or terminal (macOS/Linux).
   - Run the following command:
     ```bash
     nvcc --version
     ```
   - Look for a line like `release 11.7` in the output, which indicates the installed CUDA version.

2. **Check Your NVIDIA Driver Version**:
   - **Windows**:
     - Open the NVIDIA Control Panel.
     - Click on "System Information" at the bottom left.
     - Check the "Driver Version" field.
   - **Linux**:
     - Run the following command:
       ```bash
       nvidia-smi
       ```
     - This will display information about your GPU, including the driver and CUDA version.

### Finding the Appropriate PyTorch Installation Command:

1. Visit the [PyTorch Get Started Page](https://pytorch.org/get-started/locally/).
2. Select your operating system, package manager, and CUDA version.
3. PyTorch will provide the appropriate installation command based on your selection.

## Configuration

1. **Environment Variables**: Set the following environment variables in your system:
   - `SPEECH_KEY`: Your Azure Speech service key.
   - `SERVICE_REGION`: The region of your Azure Speech service.

2. **FFmpeg Configuration**:
   - Ensure `ffmpeg` is added to your system's PATH so it can be called from the command line.

## Running the Project

1. **Start Azure Functions Locally**:
   ```bash
   func start
   ```

2. **Access the API**:
   - The API will be available at: `http://localhost:7071/api/process_file_api`
   - You can make `POST` requests to this endpoint to transcribe audio from uploaded video files.

## Testing the API

You can use tools like [Postman](https://www.postman.com/) or `curl` to test the API.

### Example `curl` Request:
```bash
curl -X POST -F "file=@path_to_your_video_file.mp4" http://localhost:7071/api/process_file_api
```

### Using Postman:
1. Open Postman and create a new `POST` request.
2. Set the URL to: `http://localhost:7071/api/process_file_api`.
3. In the `Body` section, select `form-data` and add a key named `file` with the video file as the value.
4. Send the request to see the transcription results.

## Notes

- **GPU Acceleration**: Using CUDA can significantly speed up transcription. Ensure CUDA is installed and properly configured if using GPU.
- **Audio Processing**: The project uses FFmpeg to extract and preprocess audio from the video files. Make sure FFmpeg is installed and accessible from your command line.
- **Whisper Model**: The Whisper model used in this project can be changed (e.g., "tiny", "base", "small", "medium", "large") based on your performance needs and available resources.

Feel free to reach out if you encounter any issues or have questions!
