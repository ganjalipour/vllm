# FROM python:3.9-slim
# WORKDIR /app
# COPY common/requirements.txt /app/common/
# COPY ui/requirements.txt /app/ui/
# RUN pip install --no-cache-dir -r common/requirements.txt -r ui/requirements.txt
# COPY common /app/common
# COPY ui /app/ui
# ENTRYPOINT ["bash", "/app/ui/entrypoint.sh"]
# Use official Python image as base
# Use official Python base image

FROM python:3.12

# Set working directory
WORKDIR /app/ui

# Copy everything from current folder to working directory in container
COPY . .

# Install dependencies (update as needed)
RUN pip install -r requirements.txt

# Fix line endings and make the entrypoint executable
RUN sed -i 's/\r$//' entrypoint.sh && \
    chmod +x entrypoint.sh

# Set production environment variables
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

# Set entrypoint script
ENTRYPOINT ["./entrypoint.sh"]




