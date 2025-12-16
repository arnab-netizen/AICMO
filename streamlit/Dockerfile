FROM python:3.12-slim
WORKDIR /app

# Copy entire project
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || pip install --no-cache-dir streamlit httpx sqlalchemy python-dotenv requests

EXPOSE 8501

# CANONICAL DASHBOARD ENTRY (V2): Run operator_v2.py (modular architecture)
# Previous: streamlit_pages/aicmo_operator.py
# New: operator_v2.py (11 independent tabs, safe DB wrapping, backend HTTP wiring)
CMD ["streamlit", "run", "operator_v2.py", \
     "--server.address=0.0.0.0", "--server.port=8501"]
