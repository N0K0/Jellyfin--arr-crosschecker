FROM python:3.14-alpine
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy
WORKDIR /app/
COPY src/ src/
COPY main.py .
COPY requirements.txt .
RUN pip install -r requirements.txt
CMD ["python","main.py"]
