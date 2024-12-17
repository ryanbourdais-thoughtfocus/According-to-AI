# Detecting and labelling multiple users from audio.

This project makes use of Pyannote.audio and OpenAI API to analysis call recording to provide speaker diarization, speaker labelling and transcript JSON generation.
## Table of Content
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Project](#running-the-project)
- [Metric calculation](#metric-calculation)

---

## Prerequisites

Before running the project, make sure you have the following installed:

1. **Python 3.12.x**: Python 3.12.x must be installed on your machine. You can download it from [python.org](https://www.python.org/downloads/) or [Microsoft Store](https://apps.microsoft.com/detail/9NCVDN91XZQP?hl=en-us&gl=US&ocid=pdpshare).

2. OpenAI API Key from [OpenAI](https://platform.openai.com/signup/)

## Installation

1. **Clone the Repository**:
   ```bash
   git clone --branch feature/ATA-46 https://github.com/ryanbourdais-thoughtfocus/According-to-AI.git
   cd According-to-AI
   ```

2. **Set Up a Python Virtual Environment**:
   ```bash
   python3.12 -m venv .venv
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

## Configuration

1. **Setup .evn with your OpenAI API and HuggingFace API key in the root of the project folder**
   ```bash
   HUGGING_FACE_ACCESS_TOKEN = [YOUR-API-KEY]
   OPENAI_API_KEY = [YOUR-API-KEY]
   ```

## Running the Project

1. **Navigate to /According-to-AI folder in the terminal**

2. **Place the audio file in ./data/audio folder**
 
3. **Run the python file**
   ```bash
   python main.py
   ```

## Metric calculation
1. **Place the reference rttm file in ./data/reference folder**

2. **Run metrics_calculation**
   ```bash
   python ./metric_calculation.py
   ```

## Note

- The output pre-processed audio is saved in ./data/processed
- The output graph file is saved in ./data/graph
- The output rttm file is saved in ./data/rttm
- The output transcript file is saved in ./transcript
