FROM python:3.8


WORKDIR /data
COPY data .

WORKDIR /setup
COPY server/requirements.txt .
RUN pip install -r requirements.txt
COPY server/dist/*.whl .
RUN pip install ./*.whl
COPY server/config.json .

CMD [ "python", "-m", "aletheia.app", "--cfg", "config.json" ]
