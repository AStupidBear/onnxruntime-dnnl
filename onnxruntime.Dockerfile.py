#!/usr/bin/env python
try:
    from pydocker import DockerFile
except ImportError:
    try:
        from urllib.request import urlopen
    except ImportError:
        from urllib import urlopen
    exec(urlopen('https://raw.githubusercontent.com/AStupidBear/pydocker/master/pydocker.py').read())

import os
import sys
import tempfile
import logging

logging.getLogger('').setLevel(logging.INFO)
logging.root.addHandler(logging.StreamHandler(sys.stdout))

img = 'registry.cn-hangzhou.aliyuncs.com/astupidbear/onnxruntime:latest'
d = DockerFile(base_img='ubuntu:18.04', name=img)

d.ARG = 'PYTHON_VERSION=3.6'
d.ARG = 'ONNXRUNTIME_REPO=https://github.com/Microsoft/onnxruntime'
d.ARG = 'ONNXRUNTIME_SERVER_BRANCH=v1.3.0'
d.ARG = 'DEBIAN_FRONTEND=noninteractive'

d.RUN = '''\
apt-get update && \
apt-get install -y sudo git bash patchelf
'''

d.ENV = 'PATH=/opt/cmake/bin:$PATH'
d.RUN = 'git clone --single-branch --branch $ONNXRUNTIME_SERVER_BRANCH --recursive $ONNXRUNTIME_REPO onnxruntime'
d.RUN = '/onnxruntime/tools/ci_build/github/linux/docker/scripts/install_ubuntu.sh -p $PYTHON_VERSION'
d.RUN = '/onnxruntime/tools/ci_build/github/linux/docker/scripts/install_deps.sh -p $PYTHON_VERSION'

d.RUN = 'sed -i s/pip/pip3/g /onnxruntime/dockerfiles/scripts/install_common_deps.sh && /bin/sh /onnxruntime/dockerfiles/scripts/install_common_deps.sh'

d.WORKDIR = '/'
args = '--use_mklml --use_dnnl'
if os.getenv('USE_NGRAPH', '0') == '1':
    args = ' --use_ngraph'
if os.getenv('USE_NUPHAR', '0') == '1':
    args += ' --use_tvm --use_llvm --use_nuphar'
d.ENV = 'AUDITWHEEL_PLAT=manylinux2014_x86_64'
d.RUN = '''\
mkdir -p /onnxruntime/build && \
pip3 install sympy packaging cpufeature jupyter auditwheel && \
python3 /onnxruntime/tools/ci_build/build.py --build_dir /onnxruntime/build \
--config Release --enable_pybind --build_wheel --build_shared_lib \
--skip_tests --parallel --skip_submodule_sync %s''' % args

os.chdir(tempfile.mkdtemp())
d.build_img(extra_args='--network host')
os.system('docker run --name onnxruntime %s /bin/true' % img)
os.makedirs('/tmp/onnxruntime/', exist_ok=True)
os.system('docker cp onnxruntime:/onnxruntime/build/Release/dist /tmp/onnxruntime/')
os.system('docker rm onnxruntime')
