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
RUN pip install git+https://github.com/mit-nlp/MITIE.git
RUN pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-1.2.0/en_core_web_sm-1.2.0.tar.gz --no-cache-dir > /dev/null \
    && python -m spacy link en_core_web_sm en
RUN wget -P /usr/src/app/data/ https://s3-eu-west-1.amazonaws.com/mitie/total_word_feature_extractor.dat

# add app
ADD . /usr/src/app

# download nltk data
RUN python -m nltk.downloader stopwords

# run server
CMD gunicorn -b 0.0.0.0:5000 manage:app --timeout 3000