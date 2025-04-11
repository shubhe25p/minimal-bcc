#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[]) {
    if (argc != 3) {
        fprintf(stderr, "Usage: %s <file_path> <nbytes>\n", argv[0]);
        return 1;
    }
    
    char *file_path = argv[1];
    long nbytes = strtol(argv[2], NULL, 10);
    
    if (nbytes <= 0) {
        fprintf(stderr, "Error: Number of bytes must be positive\n");
        return 1;
    }
    
    char *buffer = (char *)malloc(nbytes);
    if (buffer == NULL) {
        fprintf(stderr, "Error: Failed to allocate memory\n");
        return 1;
    }
   
    memset(buffer, 'A', nbytes);
    
    FILE *file = fopen(file_path, "wb");
    if (file == NULL) {
        fprintf(stderr, "Error: Cannot open file %s\n", file_path);
        free(buffer);
        return 1;
    }
    
    size_t written = fwrite(buffer, 1, nbytes, file);
    if (written != nbytes) {
        fprintf(stderr, "Error: Failed to write all bytes to file\n");
    }
    
    fclose(file);  
    free(buffer);    
    printf("Successfully wrote %ld bytes to %s\n", nbytes, file_path);
    
    return 0;
}
