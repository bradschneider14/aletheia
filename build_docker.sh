#/bin/bash

pushd server
source venv/bin/activate
python setup.py bdist_wheel
deactivate
popd

docker build -t aletheia/api .

rm -rf server/dist
