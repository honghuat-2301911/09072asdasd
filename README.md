# ICT2216_Group23

## Layered ECB Architecture

### Folder Structure
```bash
ICT2216_GROUP23/
│
├── data_source/ # SQL queries and gateway logic
│
├── domain/ # Business logic layer
│ ├── control/ # Services / use-case logic
│ └── entity/ # Entity classes (e.g., User, Product)
│
├── presentation/ # Presentation layer (UI and controllers)
│ ├── controller/ # Route handlers (Flask Blueprints)
│ ├── static/ # CSS, JS, images
│ │ ├── css/ # Stylesheets
│ │ └── icons/ # Icons
│ │ └── images/ # Images 
│ └── templates/ # HTML templates (Jinja2)
│
└── app.py # Application entry point
```
Link to Class Diagram:

    https://lucid.app/lucidchart/7e476bb1-7cab-492d-981c-0ac3399b7a89/edit?viewport_loc=-1145%2C-4517%2C9443%2C4371%2CYBco9rN3~mD.&invitationId=inv_dcce0450-c77e-4b8e-a127-28534c9795ea

## 📦 Architecture Overview

- **Flask (Gunicorn)** runs the backend app (`app.py`)
- **MySQL** stores user, activity, feed, and comment data
- **Nginx** receives all HTTP requests and forwards them to Gunicorn
- **Docker Compose** orchestrates all services together

## Port Mapping

| Component | Internal Port | External (Localhost) Port | Description                         |
|-----------|---------------|----------------------------|-------------------------------------|
| Nginx     | 80            | 80                         | Public entry point (`http://localhost`) |
| Gunicorn  | 8000          | (internal only)            | Flask runs here, behind Nginx       |
| MySQL     | 3306          | 3306                       | MySQL used by Flask (not exposed to browser) |

## How It Works

1. User visits `http://localhost`
2. Nginx (on port 80) receives the request
3. Nginx forwards it to the Flask app running on Gunicorn (`web:8000`)
4. Flask app processes the request and interacts with MySQL (`mysqldb:3306`)
5. Response is sent back through Nginx to the user

## Run Locally (LOOK HERE) (need to open your docker desktop first) (run these lines in your PowerShell)

```bash
docker-compose down -v
docker-compose up --build
```
## If you only need to update web codes

```bash
docker-compose build web
docker-compose up --build
```

## If need to recreate SQL schema or restart db from scratch, need to delete mysql_data folder first before running down and up commands
