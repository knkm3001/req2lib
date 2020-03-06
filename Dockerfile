FROM python:3
USER root

RUN apt-get update && \
    apt-get install -y locales && \
    localedef -f UTF-8 -i ja_JP ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ JST-9
ENV TERM xterm

# Chrome レポジトリ署名鍵をDL
# Chrome のリポジトリを追加
# レポジトリの更新 と 安定版ChromeのDL
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \ 
    sh -c 'echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' && \
    apt-get update -y && apt-get install -y google-chrome-stable

# chromedriver-binary では chrome と chrome-driver のバージョンをあわせる処理を行ってる
RUN pip install --upgrade pip && \
    pip install beautifulsoup4 selenium  && \
    pip install chromedriver-binary~=$(/usr/bin/google-chrome --version \
        | perl -pe 's/([^0-9]+)([0-9]+\.[0-9]+).+/$2/g')

