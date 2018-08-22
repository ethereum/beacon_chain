FROM python:3.6-stretch

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "tail", "-f" "/dev/null" ]