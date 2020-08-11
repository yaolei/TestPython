FROM python:3.7.3
RUN pip install --upgrade pip
RUN pip3 install ibm_db
RUN pip3 install configparser
# RUN pip3 install django==2.0
MAINTAINER <yaoleidl@cn.ibm.com, evan>
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]