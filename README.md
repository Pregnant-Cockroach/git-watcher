#  Local LLM Git Watcher

Automated tool for local Code Reviews. 
Tracks changes in a Git repository, filters out junk files, and uses a local LLM (via Ollama) to analyze code for vulnerabilities and code smells.

## Features
* **Works locally:** Uses Ollama, no data are being saved or collected in the cloud.
* **Smart Filtering:** Parses `git diff`, excluding removed code, binary files or other files.
* **Real-time:** Watcher based on Python FastAPI tracks branch changes in real time.

## Stack
* Python 3.10+
* FastAPI (Web server & Async tasks)
* Ollama (AI Inference)
* Git CLI

## Download
1. Download dependencies: `pip install -r requirements.txt`
2. Create .env file `.env`:

    `TARGET_REPO_PATH=path`
    <br>
    `WATCH_BRANCH=branch`
    <br>
    `OLLAMA_URL=url (http://localhost:11434/api/generate by default)`
    <br>
    `MODEL=model`


3. Start: `uvicorn main:app --reload`

