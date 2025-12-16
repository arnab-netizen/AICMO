FROM python:3.12-slim
WORKDIR /app

# Copy entire project
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || pip install --no-cache-dir streamlit httpx sqlalchemy python-dotenv requests

EXPOSE 8501

# CANONICAL DASHBOARD ENTRY: Always run streamlit_pages/aicmo_operator.py
CMD ["streamlit", "run", "streamlit_pages/aicmo_operator.py", \
     "--server.address=0.0.0.0", "--server.port=8501"]
