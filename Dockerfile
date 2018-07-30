FROM python:3.6.1
LABEL AUTHOR="akshay akshay@ozz.ai"

# set working directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# add requirements (to leaverage Docker cache)
ADD ./requirements.txt /usr/src/app/requirements.txt

# install JVM
RUN apt-get update
RUN apt-get install -y default-jre

# install requirements
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm && python -m spacy link en_core_web_sm en

# add app
ADD . /usr/src/app

# run server
CMD gunicorn -b 0.0.0.0:5000 manage:app --timeout 3000