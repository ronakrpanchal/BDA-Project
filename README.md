# Plan My Diet

<div align="center">

AI-powered diet planning and meal logging with a FastAPI backend and Next.js frontend.

![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688)
![Next.js](https://img.shields.io/badge/frontend-Next.js-000000)
![SQLite](https://img.shields.io/badge/database-SQLite-0f80cc)
![Python](https://img.shields.io/badge/python-3.12-blue)
![TypeScript](https://img.shields.io/badge/typescript-5.x-3178c6)
[![Deployed on Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-black?logo=vercel)](https://bda-project-henna.vercel.app/chat)
![GitHub stars](https://img.shields.io/github/stars/ronakrpanchal/BDA-Project)
![GitHub forks](https://img.shields.io/github/forks/ronakrpanchal/BDA-Project)
![GitHub issues](https://img.shields.io/github/issues/ronakrpanchal/BDA-Project)
![GitHub last commit](https://img.shields.io/github/last-commit/ronakrpanchal/BDA-Project)
![Made with Love](https://img.shields.io/badge/Made%20with-Love-ff69b4)
![Open Source](https://img.shields.io/badge/Open%20Source-%E2%9D%A4-purple)
![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-blue.svg)

</div>

## Table of Contents

- [About](#about)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Preview](#preview)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Activity](#activity)
- [Contributors](#contributors)
- [Support](#support)

## About

PlanMyDiet is a health assistant application that helps users:

- Generate personalized diet plans.
- Log meals in natural language.
- Retrieve stored diet plans.
- Chat with an AI nutrition assistant.

The backend uses FastAPI and SQLite, while the frontend is built with Next.js and TypeScript.

## Features

- Unified AI endpoint for conversation, diet planning, and meal logging.
- Structured JSON responses from Groq LLM integration.
- SQLite persistence for users, diet plans, and meal logs.
- Modern frontend UI for chat and diet plan visualization.
- CORS-enabled API for local frontend-backend integration.

## Tech Stack

- Backend: FastAPI, Pydantic, Uvicorn, Requests, Python Dotenv
- Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS
- Database: SQLite
- AI Provider: Groq Chat Completions API

## Preview

<div align="center">

![Chat](assets/readme/chat.png)

![Diet](assets/readme/diet.png)

![Overview](assets/readme/overview.png)

![Workout](assets/readme/workout.png)

![Weekly Plan](assets/readme/weekly%20plan.png)

</div>

## Getting Started

### Prerequisites

- Python 3.12
- Node.js 18+
- pnpm

### 1. Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python db.py
uvicorn main:app --reload --port 8000
```

Backend runs at http://localhost:8000

### 2. Frontend Setup

```bash
cd frontend
pnpm install
pnpm dev
```

Frontend runs at http://localhost:3000

## Environment Variables

Create a `.env` file in the project root (or in backend if preferred by your runtime) with:

```env
GROQ_API_KEY=your_groq_api_key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Activity
![Alt](https://repobeats.axiom.co/api/embed/35e6198dbb469a1c06b704b48ea937c90c0745f4.svg "Repobeats analytics image")

## Contributors

<a href="https://github.com/ronakrpanchal/BDA-Project/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=ronakrpanchal/BDA-Project"/>
</a>

## Support
if you find the project useful, please consider giving it a star ⭐ 💫

Thank you 🤩