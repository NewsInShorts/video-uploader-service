FROM python:3.13-slim-bookworm


ENV APP_ENV=production

COPY ./requirements.txt /video-uploader-service/requirements.txt

WORKDIR /video-uploader-service

# RUN apt-get install -y build-essential gcc g++
RUN pip install -r requirements.txt
# RUN pip install playwright 
# RUN playwright install
# RUN playwright install-deps
# RUN pip install fastapi
# RUN pip install gunicorn
# RUN pip install uvicorn[standard]


# COPY . /nis-ai-tools
# ENV ELASTIC_APM_ENVIRONMENT="production"
# ENV ELASTIC_APM_SERVER_URL="http://172.15.0.179:8200"
# ENV ELASTIC_APM_SERVICE_NAME="nis-ai-tools"
# ENV ELASTIC_APM_TRANSACTION_SAMPLE_RATE=0.05
# ENV ELASTIC_APM_SPAN_COMPRESSION_SAME_KIND_MAX_DURATION="50ms"

CMD gunicorn -k uvicorn.workers.UvicornWorker --preload --bind 0.0.0.0:8080 app.main:app --workers 4 --timeout 10800