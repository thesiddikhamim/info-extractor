# 🚀 Web Extractor Pro | Multi-Model AI Intelligence

Web Extractor Pro is a premium, AI-powered intelligence dashboard designed to extract lead data, contact information, and business profiles from any website. By combining the power of **Google Gemini 2.5** and **Mistral AI**, it provides highly accurate extractions with a sleek, modern interface.

---

## ✨ Features
-   **Dual-Model Intelligence**: Switch between Google Gemini (native SDK) and Mistral AI (LiteLLM) for optimal extraction.
-   **Live Analysis Monitor**: Real-time terminal-style console to track scraping progress.
-   **Deep Scraping**: Automatically discovers contact, about, and team pages to find hidden data.
-   **Privacy First**: Your API keys are stored locally in your browser's `localStorage` and never touch our servers.
-   **Lead Export**: Export your results directly to professional CSV files.
-   **Premium UI**: A stunning dark-mode interface with glassmorphism aesthetics and smooth animations.

---

-   **Mac**: Install via [python.org](https://www.python.org/) or `brew install python`.
-   **Windows**: Install via the [Microsoft Store](https://www.microsoft.com/store/productId/9PJPW5LDXLZ5) or [python.org](https://www.python.org/). (Check "Add Python to PATH").

### 🔍 Verify Installation
Check your version by running:
```bash
python --version  # Should be 3.9+
```

---

## 📦 Installation & Setup

### 1. Set Up a Virtual Environment (Recommended)
It is highly recommended to run the app in a virtual environment to avoid dependency conflicts.

**On Mac / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 2. Install Dependencies
Once the environment is activated, install the required packages:

```bash
pip install fastapi uvicorn litellm google-genai beautifulsoup4 requests pydantic
```

> [!NOTE]
> On **Mac**, if the command fails, try using `pip3` instead of `pip`.

---

## 🏃‍♂️ Running the Application

### 🍎 On Mac
```bash
python3 -m uvicorn app:app --reload
```

### 🪟 On Windows
```powershell
python -m uvicorn app:app --reload
```

Once running, access the dashboard at:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## 📖 Detailed Usage Guide

### 1. Configure Your AI
Click the **Settings (⚙️)** icon in the top right to manage your API keys.
-   **Google Gemini**: Get your API key from [Google AI Studio](https://aistudio.google.com/).
-   **Mistral AI**: Get your API key from [Mistral Console](https://console.mistral.ai/).

### 2. Select Your Model
Choose from the dropdown in the configuration panel:
-   **Gemini 2.5 Flash**: Lightning fast, highly efficient for bulk processing.
-   **Gemini 2.5 Pro**: Powerful reasoning for complex contact pages.
-   **Mistral Large**: Smart, enterprise-grade extraction.

### 3. Input URLs
-   **File Upload**: Select a `.txt` file containing one URL per line.
-   **Manual Paste**: Directly paste URLs into the text area.

### 4. Extract and Export
Click **Start Extraction**. Watch the live monitor as the AI analyzes each page. Once finished, click **Export CSV** to download your results.

---

## 📂 Project Architecture
-   `app.py`: FastAPI backend handling model routing and streaming results.
-   `core/extractor_service.py`: The extraction engine using official `google-genai` and `litellm`.
-   `static/`: Dashboard frontend (HTML/CSS/JS) with premium aesthetics.
-   `static/favicon.png`: Custom-designed application brand icon.

---

## ⚠️ Troubleshooting
-   **ImportError**: If you see `ModuleNotFoundError`, double-check that you ran the `pip install` command.
-   **SSL Errors**: If you can't fetch websites on Mac, ensure you have run the "Install Certificates" command in your Python folder.
-   **API Limits**: Ensure your API keys have sufficient quota for extraction.

---
*Made with ❤️ by Hamim*
