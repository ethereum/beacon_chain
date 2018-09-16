FROM python:3.6-stretch

WORKDIR /usr/src/app
RUN pip install --upgrade setuptools
RUN pip install -e .[dev] --no-cache-dir 

COPY . .

CMD [ "tail", "-f" "/dev/null" ]
