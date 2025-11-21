FROM python:3.12-slim
WORKDIR /app
COPY ./app.py ./app.py
RUN pip install --no-cache-dir streamlit httpx
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
