# 📁 EZ Backend Intern Assignment

This repository contains the solution to the backend intern assessment provided by **EZ**. It is a secure file-sharing API developed using **FastAPI**, which supports role-based access control for uploading and downloading specific document types (`.docx`, `.pptx`, `.xlsx`).

---

## 🔧 Tech Stack

- **Language**: Python 3
- **Framework**: FastAPI
- **Security**: JWT (OAuth2), Fernet encryption
- **Authentication**: Role-based access (`ops`, `client`)
- **Data Storage**: In-memory (dictionary-based)
- **Package Management**: `pip` (`requirements.txt`)
- **API Testing**: Postman (collection included)

---

## 📂 Project Structure

ez-backend-intern-assignment/
├── main.py # Application logic
├── .env # Environment variables (excluded from commit)
├── requirements.txt # Project dependencies
├── uploads/ # Uploaded files directory
├── SecureFileSharingAPI.postman_collection.json # Postman API collection
└── README.md # Project documentation
---

## 🔐 Features

- User registration with role selection (client / ops)
- Email verification with secure token (simulated using Fernet)
- JWT-based login and authentication
- File upload (allowed only for 'ops' users)
- File listing and downloading (allowed only for verified 'client' users)
- Secure one-time download links
- Download history simulation

---

## 📦 Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/ez-backend-intern-assignment.git
   cd ez-backend-intern-assignment
   
2. Install Dependencies
   pip install -r requirements.txt
   
4. Setup Environment Variables
   Create a .env file with the following content:
   SECRET_KEY=your_jwt_secret_key
  ALGORITHM=HS256
  ACCESS_TOKEN_EXPIRE_MINUTES=30
  FERNET_KEY=your_fernet_key_here
  To generate a Fernet key, run:
  from cryptography.fernet import Fernet
  print(Fernet.generate_key().decode())

5. Run the Application
   uvicorn main:app --reload

6. Open in browser:
   http://127.0.0.1:8000/docs
📬 API Endpoints
Method	Endpoint	Access Role	Description
POST	/signup	Public	Register new user
GET	/verify-email/{token}	Public	Simulate email verification
POST	/login	Public	Login and get access token
POST	/upload	Ops only	Upload file
GET	/list-files	Client only	View uploaded files
GET	/download-file/{file_id}	Client only	Generate secure download link
GET	/secure-download/{token}	Client only	Secure file download
GET	/download-history	Client only	View download history

Use the included Postman collection: SecureFileSharingAPI.postman_collection.json for testing.


🧪 Testing with Postman
Import the file SecureFileSharingAPI.postman_collection.json into Postman.

Follow the flow:

Sign up (/signup)

Copy token from /verify-email/{token} and hit the route

Login via /login and use token for other requests

Upload file (as ops)

List and download file (as client)
