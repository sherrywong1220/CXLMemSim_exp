CC = gcc
CFLAGS = -O3 -Wall -Wextra -pthread -msse4.1
LDFLAGS = -lnuma -lpthread

TARGET = memstress
SRC = memstress.c

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC) $(LDFLAGS)

clean:
	rm -f $(TARGET)

# Example usage targets
run-0x:
	./$(TARGET) -n 1 -b 1024 -t 0 -c 48

run-1x:
	./$(TARGET) -n 1 -b 1024 -t 4 -c 48

run-2x:
	./$(TARGET) -n 1 -b 1024 -t 8 -c 48

run-3x:
	./$(TARGET) -n 1 -b 1024 -t 12 -c 48

run-4x:
	./$(TARGET) -n 1 -b 1024 -t 16 -c 48

.PHONY: all clean run-0x run-1x run-2x run-3x run-4x
