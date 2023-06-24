FROM python:3

RUN mkdir -p /opt/src/customer
WORKDIR /opt/src/customer

COPY customer/application.py ./application.py
COPY customer/requirements.txt ./requirements.txt
COPY store/configuration.py store/configuration.py
COPY store/models.py store/models.py

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/customer"

# ENTRYPOINT ["echo", "hello world"]
# ENTRYPOINT ["sleep", "1200"]
ENTRYPOINT ["python", "./application.py"]
