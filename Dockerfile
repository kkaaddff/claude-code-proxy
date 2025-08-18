FROM python:3.11-slim

# Copy the project into the image
ADD . /app

# Install dependencies
WORKDIR /app
RUN pip install -r requirements.txt

CMD ["python", "start_proxy.py"]