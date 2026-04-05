SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../../env.sh"


# CXL MPI Library
cd "${CXL_SHM_LIB_DIR}"
./build.sh

# Stencil
cd ${WORKLOAD_DIR}/stencil
make

