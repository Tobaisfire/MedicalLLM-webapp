# MedicLLM Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technical Stack](#technical-stack)
4. [Core Components](#core-components)
5. [Setup and Installation](#setup-and-installation)
6. [Usage Guide](#usage-guide)
7. [API Documentation](#api-documentation)
8. [Development Guidelines](#development-guidelines)

## Project Overview

MedicLLM is an AI-powered psychiatric diagnosis and treatment planning assistant developed at Lokmanya Tilak Municipal Medical College & Hospital (Sion Hospital). The system employs a multi-agent framework to provide comprehensive psychiatric care support.

### Key Features
- Multi-agent argumentative reasoning system
- Explainable AI (XAI) framework
- Modern medical chat interface
- Session management and reporting
- Admin panel for case management
- Dark/Light mode support

## System Architecture

### Core Components
1. **Frontend Layer**
   - Django templates
   - Static assets (CSS, JavaScript)
   - Chat interface
   - XAI visualization components

2. **Backend Layer**
   - Django web framework
   - Multi-agent LLM system
   - Vector database (Qdrant)
   - Session management

3. **AI Layer**
   - OpenAI integration
   - Langchain orchestration
   - Multi-agent reasoning system
   - XAI framework

## Technical Stack

### Backend Technologies
- Django 4.2+
- Python 3.x
- Qdrant Vector Database
- OpenAI API

### Frontend Technologies
- HTML/CSS
- JavaScript
- Bootstrap (inferred from project structure)

### AI/ML Technologies
- Langchain 0.1.0+
- OpenAI 1.0.0+
- NetworkX for visualization
- Pandas for data handling

### Development Tools
- Git for version control
- Docker for containerization
- SQLite for development database

## Core Components

### 1. Multi-Agent System
The system consists of three specialized agents:
- **Diagnosis Agent**: Analyzes patient symptoms and medical history
- **Medicine Agent**: Recommends appropriate medications
- **Treatment Agent**: Develops comprehensive treatment plans

### 2. XAI Framework
- Debate visualization
- Reasoning transparency
- Clinical decision support
- Evidence-based recommendations

### 3. Session Management
- Persistent chat sessions
- Patient report generation
- Case history tracking
- Admin oversight

## Setup and Installation

### Prerequisites
- Python 3.x
- OpenAI API key
- Qdrant server
- Git

### Installation Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/Tobaisfire/MedicalLLM-webapp.git
   cd MedicLLM
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   - Create `.env` file
   - Add OpenAI API key
   - Configure other environment variables

4. Database setup:
   ```bash
   python manage.py migrate
   ```

5. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Usage Guide

### For Clinicians
1. Access the web interface at `http://localhost:8000`
2. Start a new session or load existing patient data
3. Interact with the AI assistant through the chat interface
4. Review and download patient reports
5. Analyze XAI visualizations for decision support

### For Administrators
1. Access the admin panel at `/admin`
2. Monitor active sessions
3. Review case histories
4. Manage user access
5. Generate system reports

## API Documentation

### Core Endpoints
- `/api/chat/` - Chat interaction endpoint
- `/api/session/` - Session management
- `/api/report/` - Report generation
- `/api/xai/` - XAI visualization data

### Authentication
- Session-based authentication
- Admin authentication for privileged endpoints

## Development Guidelines

### Code Structure
- Follow Django project structure
- Maintain separation of concerns
- Document all major functions
- Include unit tests

### Best Practices
1. **Code Style**
   - Follow PEP 8 guidelines
   - Use meaningful variable names
   - Include docstrings

2. **Testing**
   - Write unit tests for new features
   - Maintain test coverage
   - Document test cases

3. **Security**
   - Secure API endpoints
   - Protect sensitive data
   - Follow HIPAA guidelines

4. **Performance**
   - Optimize database queries
   - Cache frequently accessed data
   - Monitor API response times

## Contributing
1. Fork the repository
2. Create a feature branch
3. Submit a pull request
4. Follow the code review process

## Support and Contact
- Primary Contact: Keval Saud (kevalsaud25@gmail.com)
- LinkedIn: [Keval Sing Saud](https://www.linkedin.com/in/keval-sing-saud-1945231b2/)

---

*This documentation is maintained by the MedicLLM development team. Last updated: [Current Date]* 