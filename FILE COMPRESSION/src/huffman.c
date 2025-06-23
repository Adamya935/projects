#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#define BYTE_RANGE 256

typedef struct HuffmanNode {
    unsigned char ch;
    int freq;
    struct HuffmanNode *left, *right;
} HuffmanNode;

typedef struct MinHeap {
    int size;
    HuffmanNode *array[BYTE_RANGE];
} MinHeap;

char *codes[BYTE_RANGE];

// --------- Min Heap and Tree --------------

HuffmanNode* create_node(unsigned char ch, int freq, HuffmanNode *left, HuffmanNode *right) {
    HuffmanNode *node = (HuffmanNode*)malloc(sizeof(HuffmanNode));
    node->ch = ch; node->freq = freq; node->left = left; node->right = right;
    return node;
}

void insert_heap(MinHeap *heap, HuffmanNode *node) {
    int i = heap->size++;
    while (i && node->freq < heap->array[(i - 1) / 2]->freq) {
        heap->array[i] = heap->array[(i - 1) / 2];
        i = (i - 1) / 2;
    }
    heap->array[i] = node;
}

HuffmanNode* extract_min(MinHeap *heap) {
    HuffmanNode *min = heap->array[0];
    HuffmanNode *last = heap->array[--heap->size];
    int i = 0;
    while (i * 2 + 1 < heap->size) {
        int smallest = i * 2 + 1;
        if (smallest + 1 < heap->size && heap->array[smallest + 1]->freq < heap->array[smallest]->freq)
            smallest++;
        if (last->freq <= heap->array[smallest]->freq) break;
        heap->array[i] = heap->array[smallest];
        i = smallest;
    }
    heap->array[i] = last;
    return min;
}

HuffmanNode* build_tree(int freq[]) {
    MinHeap heap = {0};
    for (int i = 0; i < BYTE_RANGE; i++) {
        if (freq[i]) insert_heap(&heap, create_node((unsigned char)i, freq[i], NULL, NULL));
    }
    if (heap.size == 0) return NULL;
    while (heap.size > 1) {
        HuffmanNode *left = extract_min(&heap);
        HuffmanNode *right = extract_min(&heap);
        insert_heap(&heap, create_node('\0', left->freq + right->freq, left, right));
    }
    return extract_min(&heap);
}

void generate_codes(HuffmanNode *root, char *code, int depth) {
    if (!root) return;
    if (!root->left && !root->right) {
        code[depth] = '\0';
        codes[root->ch] = strdup(code);
        return;
    }
    code[depth] = '0';
    generate_codes(root->left, code, depth + 1);
    code[depth] = '1';
    generate_codes(root->right, code, depth + 1);
}

void free_tree(HuffmanNode *root) {
    if (!root) return;
    free_tree(root->left);
    free_tree(root->right);
    free(root);
}

// -------- BitWriter ---------------

typedef struct BitWriter {
    FILE *file;
    unsigned char buffer;
    int bit_count;
} BitWriter;

void init_bitwriter(BitWriter *bw, FILE *file) {
    bw->file = file;
    bw->buffer = 0;
    bw->bit_count = 0;
}

void write_bit(BitWriter *bw, int bit) {
    bw->buffer = (bw->buffer << 1) | (bit & 1);
    bw->bit_count++;
    if (bw->bit_count == 8) {
        fputc(bw->buffer, bw->file);
        bw->bit_count = 0;
        bw->buffer = 0;
    }
}

void write_code(BitWriter *bw, const char *code) {
    for (int i = 0; code[i]; i++) write_bit(bw, code[i] == '1');
}

void flush_bits(BitWriter *bw) {
    if (bw->bit_count > 0) {
        bw->buffer <<= (8 - bw->bit_count);
        fputc(bw->buffer, bw->file);
        bw->bit_count = 0;
        bw->buffer = 0;
    }
}

// -------- BitReader --------------

typedef struct BitReader {
    FILE *file;
    unsigned char buffer;
    int bit_count;
} BitReader;

void init_bitreader(BitReader *br, FILE *file) {
    br->file = file;
    br->buffer = 0;
    br->bit_count = 0;
}

int read_bit(BitReader *br) {
    if (br->bit_count == 0) {
        int c = fgetc(br->file);
        if (c == EOF) return -1;
        br->buffer = (unsigned char)c;
        br->bit_count = 8;
    }
    int bit = (br->buffer >> 7) & 1;
    br->buffer <<= 1;
    br->bit_count--;
    return bit;
}

// -------- Write and read tree --------------

void write_tree(BitWriter *bw, HuffmanNode *root) {
    if (!root) return;
    if (!root->left && !root->right) {
        write_bit(bw, 1);
        for (int i = 7; i >= 0; i--) write_bit(bw, (root->ch >> i) & 1);
    } else {
        write_bit(bw, 0);
        write_tree(bw, root->left);
        write_tree(bw, root->right);
    }
}

HuffmanNode* read_tree(BitReader *br) {
    int bit = read_bit(br);
    if (bit == -1) return NULL;
    if (bit == 1) {
        unsigned char ch = 0;
        for (int i = 0; i < 8; i++) {
            int b = read_bit(br);
            if (b == -1) return NULL;
            ch = (ch << 1) | b;
        }
        return create_node(ch, 0, NULL, NULL);
    } else {
        HuffmanNode *left = read_tree(br);
        HuffmanNode *right = read_tree(br);
        return create_node('\0', 0, left, right);
    }
}

// -------- File size helper -----------

long file_size(const char *filename) {
    struct stat st;
    if (stat(filename, &st) == 0) return st.st_size;
    return -1;
}

// -------- Compression -------------

int compress_file(const char *input_path, const char *output_path) {
    int freq[BYTE_RANGE] = {0};
    FILE *fin = fopen(input_path, "rb");
    if (!fin) { perror("Failed to open input file"); return 1; }

    unsigned char ch;
    while (fread(&ch, 1, 1, fin) == 1) freq[ch]++;
    rewind(fin);

    HuffmanNode *root = build_tree(freq);
    if (!root) { fclose(fin); printf("No data to compress.\n"); return 1; }

    char code[256];
    generate_codes(root, code, 0);

    FILE *fout = fopen(output_path, "wb");
    if (!fout) { perror("Failed to open output file"); fclose(fin); free_tree(root); return 1; }

    BitWriter bw;
    init_bitwriter(&bw, fout);

    // Write Huffman tree
    write_tree(&bw, root);

    // Write compressed data bits
    while (fread(&ch, 1, 1, fin) == 1) write_code(&bw, codes[ch]);

    flush_bits(&bw);
    fclose(fin);
    fclose(fout);
    free_tree(root);

    for (int i = 0; i < BYTE_RANGE; i++) free(codes[i]);

    long orig_size = file_size(input_path);
    long comp_size = file_size(output_path);
    if (comp_size >= orig_size) {
        remove(output_path);
        printf("Compression not effective; output file removed.\n");
        return 2;
    }
    return 0;
}

// -------- Decompression -------------

int decompress_file(const char *input_path, const char *output_path) {
    FILE *fin = fopen(input_path, "rb");
    if (!fin) { perror("Failed to open input file"); return 1; }
    FILE *fout = fopen(output_path, "wb");
    if (!fout) { perror("Failed to open output file"); fclose(fin); return 1; }

    BitReader br;
    init_bitreader(&br, fin);

    HuffmanNode *root = read_tree(&br);
    if (!root) { fclose(fin); fclose(fout); printf("Failed to read Huffman tree.\n"); return 1; }

    HuffmanNode *current = root;
    int bit;
    while ((bit = read_bit(&br)) != -1) {
        if (bit == 0) current = current->left;
        else current = current->right;

        if (!current->left && !current->right) {
            fputc(current->ch, fout);
            current = root;
        }
    }

    free_tree(root);
    fclose(fin);
    fclose(fout);

    return 0;
}
