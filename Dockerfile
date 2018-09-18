FROM python:3.6-stretch

WORKDIR /usr/src/app

COPY . .

RUN pip install --upgrade setuptools
RUN pip install -e .[dev] --no-cache-dir

CMD [ "tail", "-f" "/dev/null" ]
