# E-Commerce Backend API

A RESTful E-Commerce Backend built using **Python, FastAPI, SQLAlchemy, and MySQL**. The project provides backend functionality for managing users, products, carts, and orders, with authentication and performance-focused features.

## Tech Stack

- **Backend:** Python, FastAPI
- **Database:** MySQL
- **ORM:** SQLAlchemy
- **Authentication:** JWT
- **Password Security:** bcrypt
- **Caching:** Redis
- **Testing:** Pytest
- **Load Testing:** Locust
- **Containerization:** Docker

## Features

- RESTful API development using FastAPI
- User authentication using JWT
- Password hashing for secure credential storage
- Role-based access control
- Product management
- Shopping cart and order management
- Product search, filtering, and pagination
- Redis caching for improved response performance
- Login rate limiting
- API testing using Pytest
- Load testing using Locust
- Docker support for containerized deployment

## Project Structure

```text
ecommerce-backend/
│
├── app/
│   ├── main.py
│   ├── models/
│   ├── schemas/
│   ├── routes/
│   ├── services/
│   └── database.py
│
├── tests/
│
├── Dockerfile
├── .dockerignore
├── .gitignore
├── requirements.txt
├── loctus.py
└── README.md
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd ecommerce-backend
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root and configure your database connection and application settings.

Keep credentials and secret keys in environment variables. Never commit your `.env` file to GitHub.

### 5. Run the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

## API Documentation

FastAPI automatically generates interactive API documentation.

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

## Testing

Run the test suite using:

```bash
pytest
```

## Load Testing with Locust

The project includes a Locust script to simulate users logging in and requesting product data.

Install Locust if it is not already installed:

```bash
pip install locust
```

Set the test credentials as environment variables:

```bash
set TEST_EMAIL=your_test_email
set TEST_PASSWORD=your_test_password
```

Run the load test:

```bash
locust -f loctus.py --host http://127.0.0.1:8000
```

Open the Locust web interface:

```text
http://localhost:8089
```

## Docker

Build the Docker image:

```bash
docker build -t ecommerce-api .
```

Run the container:

```bash
docker run -p 8000:8000 ecommerce-api
```

Make sure the required database and Redis services are available and correctly configured for the application.

## Learning Outcomes

Through this project, I explored:

- Building REST APIs using FastAPI
- Database integration using SQLAlchemy and MySQL
- JWT-based authentication and authorization
- Redis caching
- API testing with Pytest
- Load testing with Locust
- Containerizing applications using Docker

---

**Author:** Kanhu Nayak