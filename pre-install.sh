WORK_DIR=$(pwd)

# Prerequisites
sudo apt update
sudo apt install libtbb-dev -y

# Install Intel PCM (Only Intel(R) processors are supported)
cd $HOME
wget https://github.com/intel/pcm/archive/refs/tags/202502.tar.gz
tar -xzf 202502.tar.gz
rm 202502.tar.gz
cd pcm-202502
mkdir build
cd build
cmake ..
cmake --build . --parallel

