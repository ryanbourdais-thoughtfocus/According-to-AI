# Transcript analysis using LangChain and OpenAI API

This project makes use of LangChain and OpenAI API to analysis call transcript to provide call rating, call summary, sentiment analysis etc

## Table of Content
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Project](#running-the-project)

---

## Prerequisites

Before running the project, make sure you have the following installed:

1. **Python 3.8+**: Python 3.8 or later must be installed on your machine. You can download it from [python.org](https://www.python.org/downloads/).

2. OpenAI API Key from [OpenAI](https://platform.openai.com/signup/)

## Installation

1. 1. **Clone the Repository**:
   ```bash
   git clone --branch feature/ATA-35 https://github.com/ryanbourdais-thoughtfocus/According-to-AI.git
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

4. **Install Requirements**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. **Setup .evn with your OpenAI API key**
   ```bash
   OPENAI_API_KEY=YOUR-API-KEY
   ```

2. **Place the transcript JSON file in /cleaned_text folder**

## Running the Project

1. **Navigate to /src folder in the terminal**

2. **Run the python file**
   ```bash
   python main.py
   ```

## Note

- The output JSON will be placed in the /analysis_report folder
