WORK_DIR=$(pwd)

# Prerequisites
sudo apt update
sudo apt install libtbb-dev -y
sudo apt install libaio-dev libaio1 uuid-dev libnuma-dev cmake gfortran maven libreadline-dev libjemalloc-dev libdb++-dev python3 autoconf automake libtool libcapstone4 libpfm4 bpfcc-tools python3-bpfcc build-essential llvm-18 llvm-18-dev clang-18 libclang-18-dev libclang-cpp18 libpolly-18-dev llvm-18-tools libbpf-dev libedit-dev libcurl4-openssl-dev libdw-dev libpcap-dev binutils-dev libgtest-dev libcereal-dev pkg-config -y

# Ensure clang and llvm-config are pointing to the correct version
sudo update-alternatives --install /usr/bin/clang clang /usr/bin/clang-18 50
sudo update-alternatives --install /usr/bin/llvm-config llvm-config /usr/bin/llvm-config-18 50



# Install numactl
cd $HOME
sudo apt remove --purge numactl libnuma1 libnuma-dev -y
sudo apt autoremove -y
git clone git@github.com:sherrywong1220/numactl.git
cd numactl
git checkout pg_wi
./autogen.sh  
./configure --prefix=/usr --libdir=/usr/local/lib
make -j24
sudo make install
echo '/usr/local/lib' | sudo tee /etc/ld.so.conf.d/zz-local-lib.conf
sudo ldconfig

# Install GCC 7.5.0
cd $HOME
wget https://ftp.gnu.org/gnu/gcc/gcc-7.5.0/gcc-7.5.0.tar.gz
tar -xzf gcc-7.5.0.tar.gz
cd gcc-7.5.0
./contrib/download_prerequisites
# Fix error 'size of array is negative' (found in the base install of Ubuntu 20.04~22.04) (https://github.com/spack/spack/issues/16968)
wget https://raw.githubusercontent.com/jjolly/spack/6f6a1d3e7d56a95c9a09fc1ec3e6767cd457c967/var/spack/repos/builtin/packages/gcc/glibc-2.31-libsanitizer-1.patch
wget https://raw.githubusercontent.com/jjolly/spack/6f6a1d3e7d56a95c9a09fc1ec3e6767cd457c967/var/spack/repos/builtin/packages/gcc/glibc-2.31-libsanitizer-2-gcc-7.patch
patch -p1 < glibc-2.31-libsanitizer-1.patch
patch -p1 < glibc-2.31-libsanitizer-2-gcc-7.patch
mkdir build && cd build
../configure --prefix=$HOME/gcc-7.5.0 --disable-multilib --enable-languages=c,c++
make -j24
make install
$HOME/gcc-7.5.0/bin/gcc --version
$HOME/gcc-7.5.0/bin/g++ --version

# Install Python venv
cd $WORK_DIR
sudo apt install python3-venv -y
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# Install libbpf (static library, v1.6.2)
cd $HOME
git clone --branch v1.6.2 https://github.com/libbpf/libbpf.git
cd $HOME/libbpf/src
make -j24 BUILD_STATIC_ONLY=1
sudo make BUILD_STATIC_ONLY=1 install \
     PREFIX="/usr/local" \
     LIBDIR="/usr/local/lib" \
     INCLUDEDIR="/usr/local/include" \
     PKGCONFIGDIR="/usr/local/lib/pkgconfig"
sudo ldconfig

# Install bcc (v0.35.0-52-g2b73f76e)
cd $HOME
git clone https://github.com/iovisor/bcc.git
cd $HOME/bcc
git fetch --tags
git checkout v0.35.0-52-g2b73f76e
mkdir -p build
cd build
cmake .. \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX=/usr/local \
  -DLLVM_DIR=/usr/lib/llvm-18/lib/cmake/llvm \
  -DPYTHON_BUILD=OFF
make -j24
sudo make install
sudo ldconfig

# Install bpftrace (v0.24.0-e191c430)
cd $HOME
git clone https://github.com/bpftrace/bpftrace.git
cd $HOME/bpftrace
git fetch --tags
git checkout v0.24.0-e191c430
mkdir -p build
cd build
cmake .. \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_SHARED_LIBS=OFF \
  -DLLVM_DIR=/usr/lib/llvm-18/lib/cmake/llvm \
  -DLIBBPF_LIBRARIES=/usr/local/lib/libbpf.a \
  -DLIBBPF_INCLUDE_DIRS=/usr/local/include \
  -DKERNELHEADERS_DIR=/lib/modules/$(uname -r)/build
make -j24
sudo make install
sudo ldconfig

echo "✅ All eBPF tools installed:"
echo "  - bcc (v0.35.0-52-g2b73f76e)"
echo "  - libbpf: $(pkg-config --modversion libbpf)"
echo "  - bpftrace: $(bpftrace --version)"

# Install bpftool
SRC_DIR=$(readlink -f /lib/modules/$(uname -r)/build)
cd "$SRC_DIR/tools/bpf/bpftool"
make -j24
sudo make install
bpftool version

# Install DAMO
cd $HOME
git clone --branch v2.9.7 https://github.com/damonitor/damo.git

# Install AMDuProf
# download from https://www.amd.com/en/developer/uprof.html
cd $HOME
sudo apt install ./amduprof_5.1-701_amd64.deb
sudo ln -s /opt/AMDuProf_5.1-701/bin/AMDuProfCLI /usr/local/bin/AMDuProfCLI
sudo ln -s /opt/AMDuProf_5.1-701/bin/AMDuProf      /usr/local/bin/AMDuProf
sudo ln -s /opt/AMDuProf_5.1-701/bin/AMDuProfPcm   /usr/local/bin/AMDuProfPcm





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

# Install Likwid
cd $HOME
wget https://ftp.fau.de/pub/likwid/likwid-5.4.1.tar.gz
tar -xzf likwid-5.4.1.tar.gz
rm likwid-5.4.1.tar.gz
cd likwid-5.4.1
make -j24
sudo make install