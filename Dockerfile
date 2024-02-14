# Stage 1: Build the Python environment with dependencies
FROM python:3.11 as builder

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Stage 2: Build the final image with the Python environment and your app code
FROM python:3.11
WORKDIR /app
# Copy the Python environment from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

EXPOSE 7860

# Specify the command to run your Gradio app
CMD ["python", "/app/app.py"]

