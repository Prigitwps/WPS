FROM python:latest

LABEL org.opencontainers.image.source https://github.com/wpspublish/testing-scripts.git


# Install Chrome
RUN set -ex \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && google-chrome --version


#****************      AWS CLI V2   **************************************************
RUN set -ex \
    && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && aws --version \
    && rm -rf awscliv2.zip
#****************     END OF AWS CLI V2   ********************************************

#**************** Copy the files into Docker******************************************
ENV APP_ROOT=/app
ADD . /app
#**************** End of Copying Files************************************************

#**************** Install Automation Dependencies ************************************
RUN set -ex \
    && cd /app/oesLibraryPackage \
    && python setup.py install clean
# set display port to avoid crash
ENV DISPLAY=:99
EXPOSE 4444
#**************** End of Automation Dependencies *************************************

#**************** Setup WORKDIR *************************************
WORKDIR ${APP_ROOT}