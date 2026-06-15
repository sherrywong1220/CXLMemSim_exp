#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>

#define DAX_PATH "/dev/dax0.0"
#define CLEAR_SIZE (64ULL * 1024 * 1024 * 1024) /* 64 GB */

int main(void)
{
    int fd = open(DAX_PATH, O_RDWR);
    if (fd < 0) {
        perror("open " DAX_PATH);
        return 1;
    }

    void *addr = mmap(NULL, CLEAR_SIZE, PROT_READ | PROT_WRITE,
                       MAP_SHARED, fd, 0);
    if (addr == MAP_FAILED) {
        perror("mmap");
        close(fd);
        return 1;
    }

    printf("Clearing %llu bytes of %s ...\n",
           (unsigned long long)CLEAR_SIZE, DAX_PATH);

    memset(addr, 0, CLEAR_SIZE);

    munmap(addr, CLEAR_SIZE);
    close(fd);

    printf("Done.\n");
    return 0;
}
