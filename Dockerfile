FROM python:3.8


RUN apt update
RUN apt install -y ffmpeg


#WORKDIR /opencv
#RUN apt install -y  build-essential
#RUN apt install -y cmake git libgtk2.0-dev pkg-config libavcodec-dev libavformat-dev libswscale-dev
#RUN apt install -y python-dev python-numpy libtbb2 libtbb-dev libjpeg-dev libpng-dev libtiff-dev libdc1394-22-dev

#RUN wget --output-document cv.zip https://github.com/opencv/opencv/archive/4.4.0.zip
#RUN wget --output-document contrib.zip https://github.com/opencv/opencv_contrib/archive/4.4.0.zip
#RUN unzip cv.zip
#RUN unzip contrib.zip
#WORKDIR /opencv/opencv-4.4.0

#RUN mkdir build
#WORKDIR /opencv/opencv-4.4.0/build

#RUN cmake -D CMAKE_BUILD_TYPE=RELEASE \
#  -D CMAKE_INSTALL_PREFIX=/usr/local \
#  -D WITH_TBB=ON \
#  -D WITH_V4L=ON \
#  -D WITH_QT=OFF \
#  -D WITH_OPENGL=ON \
#  -D WITH_NVCUVID=OFF \
#  -D OPENCV_EXTRA_MODULES_PATH=../../opencv_contrib-4.4.0/modules \
#  -D OPENCV_ENABLE_NONFREE=ON \
#  -D WITH_JASPER=ON ..

#RUN make -j4 install 
#RUN ldconfig

WORKDIR /setup
COPY server/requirements.txt .

RUN pip install -r requirements.txt
COPY server/dist/*.whl .
RUN pip install -I ./*.whl
COPY server/config.json .

CMD [ "python", "-m", "aletheia.app", "--cfg", "config.json" ]
