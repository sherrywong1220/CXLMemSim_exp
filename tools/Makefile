CC = gcc
CFLAGS = -Wall -Wextra -O3 -std=c99 -D_GNU_SOURCE
LDFLAGS = -lnuma -lrt -pthread

TARGET = memstress
SOURCE = memstress.c

.PHONY: all clean install test

all: $(TARGET)

$(TARGET): $(SOURCE)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

clean:
	rm -f $(TARGET)

install: $(TARGET)
	sudo cp $(TARGET) /usr/local/bin/
	sudo chmod +x /usr/local/bin/$(TARGET)

test: $(TARGET)
	@echo "运行 memstress 测试示例..."
	./test_examples.sh

help:
	@echo "可用目标:"
	@echo "  all      - 编译 memstress"
	@echo "  clean    - 清理编译文件"
	@echo "  install  - 安装到 /usr/local/bin/"
	@echo "  test     - 运行测试示例"
	@echo "  help     - 显示此帮助信息"

# 检查依赖
check-deps:
	@echo "检查编译依赖..."
	@which gcc > /dev/null || (echo "错误: 需要安装 gcc" && exit 1)
	@echo "#include <numa.h>" | gcc -x c -E - -o /dev/null 2>/dev/null || \
		(echo "错误: 需要安装 libnuma-dev (Ubuntu/Debian) 或 numactl-devel (RHEL/CentOS)" && exit 1)
	@echo "所有依赖都已满足!"
