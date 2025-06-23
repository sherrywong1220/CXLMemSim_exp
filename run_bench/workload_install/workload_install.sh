# faster
WORKLOAD_INSTALL_DIR=$(pwd)
WORKLOAD_DIR=/mnt/nvme01/sherry/workloads

cd ${WORKLOAD_DIR}
sudo apt update
sudo apt install libtbb-dev -y
sudo apt install libaio-dev libaio1 uuid-dev libnuma-dev cmake -y

git clone https://github.com/yuhong-zhong/FASTER.git
cd FASTER/cc
mkdir -p build/Release
cd build/Release
cmake -DCMAKE_BUILD_TYPE=Release ../..
make pmem_benchmark

# redis
cd ${WORKLOAD_DIR}
wget https://github.com/redis/redis/archive/refs/tags/7.2.3.tar.gz
tar -xzvf 7.2.3.tar.gz
mv redis-7.2.3 redis
cd redis
make -j8
sudo bash -c "echo 'vm.overcommit_memory=1' >> /etc/sysctl.conf"
sed -i -e '$a save ""' redis.conf

# memcached
cd ${WORKLOAD_DIR}
sudo apt-get update
sudo apt-get install memcached -y

# ycsb
cd ${WORKLOAD_DIR}
git clone https://github.com/brianfrankcooper/YCSB.git
cd YCSB
mvn -pl site.ycsb:redis-binding -am clean package
mvn -pl site.ycsb:memcached-binding -am clean package

# NPB
cd ${WORKLOAD_DIR}
wget https://www.nas.nasa.gov/assets/npb/NPB3.4.3.tar.gz
tar -xzf NPB3.4.3.tar.gz
cd NPB3.4.2/NPB3.4-OMP
make suite CLASS=B
make suite CLASS=C
make suite CLASS=D

# GAP
cd ${WORKLOAD_DIR}
git clone https://github.com/sbeamer/gapbs.git
cp ${WORKLOAD_INSTALL_DIR}/GAP/bench.diff gapbs/benchmark/bench.mk
cd gapbs
make -j8
make bench-graphs

# DLRM
# install Intel vtune
# install miniconda
conda create --name dlrm_cpu python=3.9 ipython -y
conda activate dlrm_cpu
conda install -n dlrm_cpu astunparse cffi cmake dataclasses future mkl mkl-include ninja \
        pyyaml requests setuptools six typing_extensions -y
conda install -n dlrm_cpu -c conda-forge jemalloc gcc=12.1.0 -y
conda run -n dlrm_cpu python -m pip install git+https://github.com/mlperf/logging
conda run -n dlrm_cpu python -m pip install onnx lark-parser hypothesis tqdm scikit-learn
echo "DLRM-SETUP: FINISHED SETTING UP CONDA ENV"

mkdir -p ${WORKLOAD_DIR}/dlrm
cd dlrm
export BASE_PATH=$(pwd)

cd $BASE_PATH
git clone --recursive -b v1.12.1 https://github.com/pytorch/pytorch
cd pytorch
conda run --no-capture-output -n dlrm_cpu python -m pip install -r requirements.txt
export CMAKE_PREFIX_PATH=${CONDA_PREFIX:-"$(dirname $(which conda))/../"}
echo CMAKE_PREFIX_PATH=$CMAKE_PREFIX_PATH >> $BASE_PATH/paths.export
export TORCH_PATH=$(pwd)
echo TORCH_PATH=$TORCH_PATH >> $BASE_PATH/paths.export
conda run -n dlrm_cpu python -m pip install 'numpy<2' 
conda run --no-capture-output -n dlrm_cpu python setup.py clean
unset CPATH CPLUS_INCLUDE_PATH C_INCLUDE_PATH
conda run --no-capture-output -n dlrm_cpu python setup.py develop
echo "DLRM-SETUP: FINISHED BUILDLING PYTORCH"

cd $BASE_PATH
git clone --recursive -b v1.12.300 https://github.com/intel/intel-extension-for-pytorch
cd intel-extension-for-pytorch
export IPEX_PATH=$(pwd)
echo IPEX_PATH=$IPEX_PATH >> $BASE_PATH/paths.export
echo "DLRM-SETUP: FINISHED CLONING IPEX"

cd $BASE_PATH
git clone https://github.com/NERSC/itt-python
cd itt-python
git checkout 3fb76911c81cc9ae5ee55101080a58461b99e11c
export VTUNE_PROFILER_DIR=/opt/intel/oneapi/vtune/latest
echo VTUNE_PROFILER_DIR=$VTUNE_PROFILER_DIR >> $BASE_PATH/paths.export
conda run --no-capture-output -n dlrm_cpu python setup.py install --vtune=$VTUNE_PROFILER_DIR
echo "DLRM-SETUP: FINISHED BUILDLING ITT-PYTHON"

# Set up DLRM inference test.
cd $BASE_PATH
git clone https://github.com/rishucoding/reproduce_isca23_cpu_DLRM_inference
cd reproduce_isca23_cpu_DLRM_inference
export DLRM_SYSTEM=$(pwd)
echo DLRM_SYSTEM=$DLRM_SYSTEM >> $BASE_PATH/paths.export
# git clone -b pytorch-r1.12-models https://github.com/IntelAI/models.git
git clone -b pytorch-r1.12-models https://github.com/intel/ai-reference-models.git
cd models
export MODELS_PATH=$(pwd)
echo MODELS_PATH=$MODELS_PATH >> $BASE_PATH/paths.export
mkdir -p models/recommendation/pytorch/dlrm/product

cp $DLRM_SYSTEM/dlrm_patches/dlrm_data_pytorch.py \
    models/recommendation/pytorch/dlrm/product/dlrm_data_pytorch.py
cp $DLRM_SYSTEM/dlrm_patches/dlrm_s_pytorch.py \
    models/recommendation/pytorch/dlrm/product/dlrm_s_pytorch.py
echo "DLRM-SETUP: FINISHED SETTING UP DLRM TEST"

cd $IPEX_PATH
git apply $DLRM_SYSTEM/dlrm_patches/ipex.patch
find . -type f -exec sed -i 's/-Werror//g' {} \;
USE_NATIVE_ARCH=1 CXXFLAGS="-D_GLIBCXX_USE_CXX11_ABI=0" conda run --no-capture-output -n dlrm_cpu python setup.py install
echo "DLRM-SETUP: FINISHED BUILDING IPEX"

conda deactivate dlrm_cpu

# Liblinear
cd ${WORKLOAD_DIR}
wget https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/multicore-liblinear/liblinear-multicore-2.47.zip
unzip liblinear-multicore-2.47.zip
cd liblinear-multicore-2.47
make -j8
mkdir -p datasets
cd datasets
wget https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/binary/kddb.bz2
bunzip2 kddb.bz2
wget https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/binary/avazu-site.tr.bz2
bunzip2 avazu-site.tr.bz2


# tpc-h
cd ${WORKLOAD_DIR}

sudo cp /etc/apt/sources.list /etc/apt/sources.list~
sudo sed -Ei 's/^# deb-src /deb-src /' /etc/apt/sources.list
sudo apt-get update
sudo apt-get build-dep postgresql -y

sudo apt-get install graphviz libreadline-dev zlib1g-dev pgagent libpq5 libssl-dev libxslt1-dev build-essential python2 python2-dev python3-pip -y
sudo apt-get install libwxgtk-media3.0-gtk3-dev -y
sudo pip install sphinxcontrib-htmlhelp

cd ${WORKLOAD_DIR}
wget http://ftp.postgresql.org/pub/source/v9.3.0/postgresql-9.3.0.tar.gz
tar -zxvf postgresql-9.3.0.tar.gz
cd postgresql-9.3.0/
CFLAGS="-fno-omit-frame-pointer -rdynamic -O2" ./configure --prefix=/usr/local --enable-debug
make -j$(grep -c ^processor /proc/cpuinfo)
sudo make install

cd ${WORKLOAD_DIR}
git clone https://github.com/pgadmin-org/pgadmin3.git
cd pgadmin3
./bootstrap
CXXFLAGS="-Wno-narrowing" ./configure --prefix=/usr --with-wx-version=3.0 --with-openssl=no
sudo sed -i "s|protected:||" /usr/include/wx-3.0/wx/unix/stdpaths.h
make -j$(grep -c ^processor /proc/cpuinfo)
sudo make install

cd ${WORKLOAD_DIR}
git clone https://github.com/yuhong-zhong/pg-tpch.git
cd pg-tpch
./tpch_prepare