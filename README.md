# According-to-AI

## Project Setup

Follow these steps to set up and run the project:

### Prerequisites

- Python 3.x installed on your system.
- `git` installed for cloning the repository.

### Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/ryanbourdais-thoughtfocus/According-to-AI.git
   cd According-to-AI
   ```

2. **Create a Virtual Environment:**

   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment:**

   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install Required Packages:**

   ```bash
   pip install -r requirements.txt
   ```

   If `requirements.txt` is not available, manually install the necessary packages:

   ```bash
   pip install Flask python-dotenv fpdf langchain_openai
   ```

5. **Set Up Environment Variables:**

   Create a `.env` file in the root directory and add the necessary environment variables, such as:

   ```
   OPENAI_API_KEY=your_openai_api_key
   ```

### Running the Application

**Using Flask's Built-in Server:**

   1. Set the `FLASK_APP` environment variable:
     - On Windows Command Prompt:
       ```bash
       set FLASK_APP=app.py
       ```
     - On PowerShell:
       ```bash
       $env:FLASK_APP = "app.py"
       ```
     - On macOS/Linux:
       ```bash
       export FLASK_APP=app.py
       ```

   2. Run the application:
     ```bash
     flask run
     ```

### Access the Application

Open a web browser and go to `http://127.0.0.1:5000/` to access the application.

### Troubleshooting

- Ensure all dependencies are installed and the virtual environment is activated.
- Verify that the environment variables are correctly set in the `.env` file.

### Additional Information

For more details, refer to the [project documentation](https://github.com/yourusername/According-to-AI-UI).
