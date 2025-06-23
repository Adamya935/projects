CC=gcc
CFLAGS=`pkg-config --cflags gtk+-3.0`
LIBS=`pkg-config --libs gtk+-3.0`

all: gui

gui: gui.c huffman.c huffman.h
	$(CC) gui.c huffman.c -o gui $(CFLAGS) $(LIBS)

clean:
	rm -f gui
