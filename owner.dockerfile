FROM python:3

RUN mkdir -p /opt/src/owner
WORKDIR /opt/src/owner

COPY owner/application.py ./application.py
COPY owner/requirements.txt ./requirements.txt
COPY store/configuration.py store/configuration.py
COPY store/models.py store/models.py

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/owner"

# ENTRYPOINT ["echo", "hello world"]
# ENTRYPOINT ["sleep", "1200"]
ENTRYPOINT ["python", "./application.py"]
