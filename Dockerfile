FROM python:2.7
LABEL maintainer="Thomas Robertz"

# Setup the application.
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

# Command to run on container start. 
# This will initialize the database and run the app.
CMD [ "sh", "docker-cmd.sh" ]

# Expose the application on port 3111.
EXPOSE 3111/tcp