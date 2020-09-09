#/bin/bash

pushd server
python setup.py bdist_wheel
popd

mkdir data
cp /media/sf_share/NN_3/*.h5 data

docker build -t testimage .

rm -rf data
