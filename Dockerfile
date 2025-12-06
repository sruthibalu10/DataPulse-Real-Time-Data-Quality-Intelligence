FROM python:3.12-slim

WORKDIR /app
COPY . /app/

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8050

CMD ["python", "-c", "from app import app; app.run_server(debug=True, host='0.0.0.0')"]