# Project Phase-1 Report                                TeamID: 35

## Explanation of Each Command:

### SOURCE
	Syntax: SOURCE <filename>
The SOURCE command reads a query file (with a .ra extension) located in the /data directory and executes all the queries contained within it. This file may include commands such as LOAD MATRIX, PRINT MATRIX, EXPORT MATRIX, etc.

##### Logic:
The command reads the file line-by-line.

Each query is parsed and dispatched to the appropriate command handler.

The query file name is provided without the extension; the system appends .ra automatically.

##### Error Handling:
If the file cannot be found or opened, an error message is returned.

Each query is validated before execution; if a query is malformed, the system logs an error and continues with the next command.

### LOAD
	Syntax: LOAD MATRIX <matrix_name>
The LOAD command reads a square matrix from a CSV file, processes it, and stores it in sub-matrices fitting in a page.
##### Logic:
The matrix is first read entirely into memory.

A dynamic block (sub-matrix) size is computed based on the available page size (BLOCK_SIZE). We determine the block dimensions (i.e., maxRowsPerBlock and maxColsPerBlock) dynamically by ensuring that each square block fits within (BLOCK_SIZE * 1000) bytes.

Each block stores about 15*15 size sub-matrix.

The matrix is partitioned into square blocks. For instance, if the matrix does not divide evenly by the block size, the last block in each row or column may be smaller.

##### Error Handling:
If the CSV file is missing or empty, an error is reported.

If rows are of unequal length (matrix is not square), the command fails.

Exceptions during file I/O are caught and logged.

### PRINT
	Syntax: PRINT MATRIX <matrix_name>
PRINT MATRIX reassembles a stored matrix from its blocks and prints it to the terminal.

##### Logic:
Calculate the number of row and column blocks based on mat_size, maxRowsPerBlock, and maxColsPerBlock.

Reassemble the full matrix by loading the corresponding pages (blocks) from disk. Blocks are loaded using the Page constructor, which reads the stored sub-matrix.

Copy the data from each block into a full 2D array based on the block’s global starting indices.

Print the full matrix row-by-row.

Row_count is displayed at the end.

##### Error Handling:
If any required block is missing or fails to load, an error message is displayed.

The system validates that the reassembled matrix dimensions match the expected mat_size.

### EXPORT
	Syntax: EXPORT MATRIX <matrix_name>
EXPORT MATRIX reconstructs the matrix from its stored sub-matrices and exports it as a CSV file in the /data directory.

##### Logic:
Reassemble the full matrix from its blocks using logic similar to that in PRINT MATRIX.

Write the matrix to a CSV file in row–column order:

Each row is written on a new line.

Elements within a row are comma-separated.

The file is stored in the /data directory, with the CSV extension appended automatically.

##### Error Handling:

The system checks that it can write to the /data directory.

File I/O exceptions are caught, and a descriptive error is logged if the export fails.

Incomplete or malformed data in the stored blocks results in an export error.


### ROTATE
	Syntax: ROTATE <matrix_name>

The code implements a block-wise 90-degree rotation of a large matrix stored in pages using a buffer manager. The $subMatrixTranspose()$ function transposes a given sub-matrix by swapping its rows and columns. The $rotate()$ function iterates through the matrix in blocks of size blockLength x blockLength, identifying the correct rotated position for each block using $newRow = pageCol$ and $newCol = blockLength - 1 - pageRow$ . If the block is on the diagonal $(pageRow == pageCol)$, it is transposed and reversed in place; otherwise, it is swapped with its corresponding rotated block after both are transposed and reversed. The function reads and writes matrix pages using $bufferManager.readPage()$ and $bufferManager.writePage()$, ensuring memory efficiency by processing one block at a time and clearing the buffer after each operation.

### CROSSTRANSPOSE
	Syntax: CROSSTRANSPOSE <matrix_name1> <matrix_name2>

The $crossTranspose()$ function performs a block-wise cross-transposition between two matrices (this and matrix2), swapping corresponding transposed sub-matrices between them. It iterates over the matrix in blocks of size blockLength x blockLength, transposing each sub-matrix using $subMatrixTranspose()$. If a block lies on the diagonal $(pageRowCounter == pageColCounter)$, it is transposed and swapped directly between the two matrices. For non-diagonal blocks, it reads four corresponding sub-matrices (two from each matrix), transposes them, and swaps their positions across both matrices. The function ensures efficient memory management by reading and writing matrix pages using $bufferManager.readPage()$ and $bufferManager.writePage()$, with $bufferManager.clearBuffer()$ used to free memory after each iteration.

### CHECKANTISYM
	Syntax: CHECKANTISYM <matrix_name1> <matrix_name2>

The $checkAntiSym()$ function verifies whether a matrix is anti-symmetric by checking if $A=−A^T$  at the block level. It iterates over the matrix in blocks of size blockLength x blockLength, comparing each block with its transposed counterpart using $checkSubMatrixAntiSym()$. The $checkSubMatrixAntiSym()$ function transposes subMatrix2 and verifies that each element satisfies $Aij=−Aji$​. If any element fails this condition, the function returns false immediately. The function efficiently manages memory using $bufferManager.readPage()$ to read blocks and $bufferManager.clearBuffer()$ to free memory after each check.


## Assumptions:

1. Matrix is a square matrix always.
2. Table names and matrix names are never same.


## Contribution:

Source, code - Renu Sree Vyshnavi
Print, export - R. Shaanal
Rotate, check antisym, cross transpose - Bhumika Joshi


________________________________________________________________


