# Care Coordinator Assistant
Chatbot application for assisting providers in coordinating care for patients.
Uses the [ReAct](https://www.promptingguide.ai/techniques/react) pattern.

### Services
 - Third Party API - returns patient information (stubbed for single patient)
 - Care Coordinator Assistant API - core agentic functionality
 - Care Coordinator Assistant Client - UI (Streamlit)

### To Run (via Dockerized Services):
1) Ensure docker is installed and daemon is running
2) Run `export OPENAI_API_KEY=your_api_key`
3) Run `docker compose up` in project root
4) Open `http://localhost:8501` in your browser

### Dev Notes

This project uses [uv](https://docs.astral.sh/uv/) for python dependency management for the client and app. To run outside of docker, ensure uv is installed, then run `uv sync` in each subproject directory.

Pre-commit hooks are used to enforce code quality. To install the pre-commit hooks, run `pre-commit install` after activating the root virtual environment. To run the pre-commit hooks, run `pre-commit run --all-files`
