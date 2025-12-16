#  Local LLM Git Watcher

Automized tool for Code Reviews that works locally.
Tracks new changes in Git-repository, filters junk-files and uses local LLM model (using ollama) for code analyze to find any vulnerabilities.


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