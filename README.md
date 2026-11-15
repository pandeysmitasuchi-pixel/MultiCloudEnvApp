# MultiCloudEnvApp

A full-stack application using Flask for both frontend and backend services, demonstrating environment-specific (dev and prod) ticket management with MongoDB and Docker Compose.

Project Structure
multienv/
├── .gitignore
├── README.md
├── docker-compose.yml
├── backend/
│   ├── dev/
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .env.example
│   └── prod/
│       ├── app.py
│       ├── requirements.txt
│       ├── Dockerfile
│       └── .env.example
└── frontend/
    ├── app.py
    ├── requirements.txt
    ├── Dockerfile
    ├── .env.example
    └── templates/
        └── index.html
Setup & Running Locally
Configure Environment Files: Copy each .env.example to .env in backend/dev/, backend/prod/, and frontend/ and add your MongoDB URIs and API secrets.

cp backend/dev/.env.example backend/dev/.env
cp backend/prod/.env.example backend/prod/.env
cp frontend/.env.example frontend/.env
Run with Docker Compose:

docker-compose up --build
Access the Application:

Frontend Dashboard: http://localhost:3000/
Development Backend API: http://localhost:3001/dev
Production Backend API: http://localhost:3002/prod
Security Considerations
.env files are excluded in .gitignore so secrets are never pushed to GitHub.
Separate MongoDB databases (tickets_dev and tickets_prod) isolate development and production data.
API key authentication (X-API-Key) and HTTP security headers are enforced on all services.
