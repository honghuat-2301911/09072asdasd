FROM python:3.13-slim

# Set the working directory inside the container
WORKDIR /app

# Copy dependency file and install
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy everything (including app.py and folders)
COPY . .

# Run Flask app via Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:create_app()"]


