# 🚀 Web Extractor Pro

An AI-powered intelligence dashboard that extracts leads, contact information, and business profiles from websites using Mistral AI.

---

## 📋 Table of Contents
1. [Prerequisites](#-prerequisites)
2. [Installation](#-installation)
3. [Running the App](#-running-the-app)
4. [Usage Guide](#-usage-guide)
5. [Troubleshooting](#-troubleshooting)

---

## 🛠 Prerequisites
You need **Python 3.9 or higher** installed on your system.
- **Mac**: Usually comes with Python, but we recommend the latest version from [python.org](https://www.python.org/).
- **Windows**: Install via the Microsoft Store or [python.org](https://www.python.org/). (Ensure "Add Python to PATH" is checked during installation).

---

## 📦 Installation
Open your terminal (Mac) or Powerpulse/Command Prompt (Windows) in this project folder and run:

```bash
# Install all required libraries
pip install fastapi uvicorn litellm beautifulsoup4 requests google-genai
```

> [!NOTE]
> On **Mac**, you might need to use `pip3` instead of `pip`.

---

## 🏃‍♂️ Running the App

### 🍎 On Mac
Open Terminal in the project folder and run:
```bash
python3 -m uvicorn app:app --reload
```

### 🪟 On Windows
Open PowerShell or CMD in the project folder and run:
```powershell
python -m uvicorn app:app --reload
```

After running the command, open your browser and go to:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## 📖 Usage Guide
1. **AI Model**: Select your preferred AI model (Mistral Large, Codestral, etc.) from the dropdown. 
2. **API Key**: Enter the API key for your selected model. 
   - Get **Mistral** keys at [Mistral Console](https://console.mistral.ai/).
   - Get **OpenAI** keys at [OpenAI Dashboard](https://platform.openai.com/api-keys).
3. **URLs**: Paste the list of websites you want to analyze (one per line).
4. **Extract**: Click **Start Extraction** and watch the AI process the data in the live monitor.
5. **Export**: Once complete, click **Export CSV** to save your leads.

---

## 📂 Project Structure
- `app.py`: The backend server.
- `core/extractor_service.py`: The AI & Scraper "brain".
- `static/`: The visual dashboard dashboard (HTML/CSS/JS).

---

## ⚠️ Troubleshooting
- **ModuleNotFoundError**: Ensure you ran the `pip install` command above.
- **API Key Error**: Double check your API key is active in the settings.
- **Port 8000 in use**: If the app fails to start, you might have another server running. Close it or change the port in `app.py`.

---
*Made with ❤️ by Hamim | © 2026 Web Extractor Pro*
