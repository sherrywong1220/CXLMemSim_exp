WORKLOAD_INSTALL_DIR=$(pwd)
WORKLOAD_DIR=/home/sherry/workloads

# NPB
cd ${WORKLOAD_DIR}/
# wget https://www.nas.nasa.gov/assets/npb/NPB3.4.2.tar.gz
cp ${WORKLOAD_INSTALL_DIR}/NPB/NPB3.4.2.tar.gz ./
tar -xzf NPB3.4.2.tar.gz
rm NPB3.4.2.tar.gz
cd NPB3.4.2/NPB3.4-OMP
make suite CLASS=B
make suite CLASS=C
make suite CLASS=D

# GAP
cd ${WORKLOAD_DIR}/
git clone https://github.com/sbeamer/gapbs.git
cp ${WORKLOAD_INSTALL_DIR}/GAP/bench.diff gapbs/benchmark/bench.mk
cd gapbs
make -j8
make bench-graphs

# faster
cd ${WORKLOAD_DIR}/
git clone https://github.com/yuhong-zhong/FASTER.git
cd FASTER/cc
mkdir -p build/Release
cd build/Release
cmake -DCMAKE_BUILD_TYPE=Release ../..
make pmem_benchmark

# redis
cd ${WORKLOAD_DIR}/
wget https://github.com/redis/redis/archive/refs/tags/7.2.3.tar.gz
tar -xzvf 7.2.3.tar.gz
mv redis-7.2.3 redis
cd redis
make -j8
sudo bash -c "echo 'vm.overcommit_memory=1' >> /etc/sysctl.conf"
sed -i -e '$a save ""' redis.conf

# memcached
cd ${WORKLOAD_DIR}/
sudo apt-get update
sudo apt-get install memcached -y

# ycsb
cd ${WORKLOAD_DIR}/
git clone https://github.com/brianfrankcooper/YCSB.git
cd YCSB
mvn -pl site.ycsb:redis-binding -am clean package
mvn -pl site.ycsb:memcached-binding -am clean package

# Silo
cd ${WORKLOAD_DIR}/
# git clone https://github.com/stephentu/silo.git
cp ${WORKLOAD_INSTALL_DIR}/Silo/silo.tar.gz ./
tar -xzf silo.tar.gz
rm silo.tar.gz
cd silo
# Compile Berkeley DB with GCC 7.5.0 for compatibility
echo "Compiling Berkeley DB with GCC 7.5.0..."
mkdir -p berkeleydb_build && cd berkeleydb_build
# wget https://download.oracle.com/berkeley-db/db-5.3.28.tar.gz
# tar -xzf db-5.3.28.tar.gz
cd db-5.3.28
cd build_unix
../dist/configure --prefix=${WORKLOAD_DIR}/silo/berkeleydb_install \
    --enable-cxx --disable-shared --enable-static \
    CC=$HOME/gcc-7.5.0/bin/gcc \
    CXX=$HOME/gcc-7.5.0/bin/g++
make -j20 -s
make install
cd ${WORKLOAD_DIR}/silo
echo "Compiling Silo with GCC 7.5.0 and custom Berkeley DB..."
LD_LIBRARY_PATH=$HOME/gcc-7.5.0/lib64:$LD_LIBRARY_PATH \
CC=$HOME/gcc-7.5.0/bin/gcc \
CXX=$HOME/gcc-7.5.0/bin/g++ \
MODE=perf make -j32 dbtest


# tpc-h
cd ${WORKLOAD_DIR}/
sudo cp /etc/apt/sources.list /etc/apt/sources.list~
sudo sed -Ei 's/^# deb-src /deb-src /' /etc/apt/sources.list
sudo apt-get update
sudo apt-get build-dep postgresql -y

sudo apt-get install graphviz libreadline-dev zlib1g-dev pgagent libpq5 libssl-dev libxslt1-dev build-essential python2 python2-dev python3-pip pkg-config gettext -y
sudo apt-get install -y \
  libgtk-3-dev libglib2.0-dev libpango1.0-dev libcairo2-dev \
  libatk1.0-dev libgdk-pixbuf-2.0-dev \
  libx11-dev libxext-dev libxrender-dev libxrandr-dev libxi-dev \
  libxinerama-dev libxcursor-dev libsm-dev libice-dev
# For Ubuntu 24.04, install libwxgtk3.2-dev instead of libwxgtk-media3.0-gtk3-dev
# sudo apt-get install libwxgtk-media3.0-gtk3-dev -y
sudo apt-get install libwxgtk3.2-dev -y
# sudo pip install sphinxcontrib-htmlhelp
# For Ubuntu 24.04’s PEP 668 protection, to install Python packages system-wide,try apt install python3-xyz, where xyz is the package you are trying to install.
sudo apt-get install python3-sphinxcontrib.htmlhelp -y

# install wx 3.0
mkdir -p ${HOME}/src && cd ${HOME}/src
curl -LO https://github.com/wxWidgets/wxWidgets/releases/download/v3.0.5/wxWidgets-3.0.5.tar.bz2
tar -xjvf wxWidgets-3.0.5.tar.bz2
cd wxWidgets-3.0.5
cd build
../configure --prefix=/opt/wx-3.0 --with-gtk=3 --enable-unicode
make -j32
sudo make install

cd ${WORKLOAD_DIR}/
wget http://ftp.postgresql.org/pub/source/v9.3.0/postgresql-9.3.0.tar.gz
tar -zxvf postgresql-9.3.0.tar.gz
rm postgresql-9.3.0.tar.gz
cd postgresql-9.3.0/
CFLAGS="-fno-omit-frame-pointer -rdynamic -O2" ./configure --prefix=/usr/local --enable-debug
make -j32
sudo make install

cd ${WORKLOAD_DIR}/
git clone https://github.com/pgadmin-org/pgadmin3.git
cd pgadmin3
./bootstrap
export PATH=/opt/wx-3.0/bin:$PATH
export LD_LIBRARY_PATH=/opt/wx-3.0/lib:$LD_LIBRARY_PATH
export PKG_CONFIG_PATH=/opt/wx-3.0/lib/pkgconfig:$PKG_CONFIG_PATH
export WX_CONFIG=/opt/wx-3.0/bin/wx-config   
CXXFLAGS="-Wno-narrowing" WX_CONFIG=/opt/wx-3.0/bin/wx-config ./configure --with-wx=/opt/wx-3.0 --with-wx-version=3.0 --prefix=/usr --with-openssl=no
sudo sed -i "s|protected:||" /opt/wx-3.0/include/wx-3.0/wx/unix/stdpaths.h
sed -i "s/extensions = \[\]/extensions = ['sphinxcontrib.htmlhelp']/" docs/en_US/conf.py
cd docs/en_US && make -f Makefile.sphinx SPHINXBUILD=/usr/bin/sphinx-build htmlhelp
cd ${WORKLOAD_DIR}/pgadmin3
make -j32
sudo make install

cd ${WORKLOAD_DIR}/
git clone https://github.com/yuhong-zhong/pg-tpch.git
cd pg-tpch
./tpch_prepare
cp ${WORKLOAD_INSTALL_DIR}/tpch/tpch-postgresql.conf $HOME/pgdata10GB/postgresql.conf
chmod 600 $HOME/pgdata10GB/postgresql.conf

# Liblinear
cd ${WORKLOAD_DIR}/
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

# Intel MLC
cd $HOME
wget https://downloadmirror.intel.com/834254/mlc_v3.11b.tgz
tar -xzvf mlc_v3.11b.tgz
rm mlc_v3.11b.tgz
sudo mv Linux/mlc /usr/local/bin/mlc

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
