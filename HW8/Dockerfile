FROM python:3.7
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
ENV GOOGLE_APPLICATION_CREDENTIALS='/usr/src/app/credentials.json'
EXPOSE 8080
CMD [ "python", "main.py" ]