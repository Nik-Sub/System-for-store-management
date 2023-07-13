FROM python:3

RUN mkdir -p /opt/src/courier
WORKDIR /opt/src/courier

COPY courier/application.py ./application.py
COPY courier/requirements.txt ./requirements.txt
COPY store/configuration.py store/configuration.py
COPY store/models.py store/models.py
COPY solidity solidity

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/customer"

# ENTRYPOINT ["echo", "hello world"]
# ENTRYPOINT ["sleep", "1200"]
ENTRYPOINT ["python", "./application.py"]
