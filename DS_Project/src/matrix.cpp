#include "global.h"

/**
 * @brief Construct a new Matrix:: Matrix object
 *
 */
Matrix::Matrix()
{
    logger.log("Matrix::Matrix");
}

/**
 * @brief Construct a new Matrix:: Matrix object used in the case where the data
 * file is available and LOAD command has been called. This command should be
 * followed by calling the load function;
 *
 * @param matrixName
 */
Matrix::Matrix(string matrixName)
{
    logger.log("Matrix::Matrix");
    this->sourceFileName = "../data/" + matrixName + ".csv";
    this->matrixName = matrixName;
}

/**
 * @brief The load function is used when the LOAD command is encountered. It
 * reads data from the source file, splits it into blocks and updates table
 * statistics.
 *
 * @return true if the table has been successfully loaded
 * @return false if an error occurred
 */
bool Matrix::load()
{
    logger.log("Matrix::load");
    fstream fin(this->sourceFileName, ios::in);
    string line, word;

    if (!getline(fin, line)) {
        fin.close();
        return false;  // File is empty
    }

    // Determine the number of columns (mat_size)
    stringstream s(line);
    int colCount = 0;
    while (getline(s, word, ',')) {
        word.erase(std::remove_if(word.begin(), word.end(), ::isspace), word.end());
        colCount++;
    }
    
    this->mat_size = colCount;
    this->maxRowsPerBlock = (uint)((BLOCK_SIZE * 1000) / (sizeof(int) * this->mat_size));
    this->blockLength = ceil((float)mat_size / this->maxRowsPerBlock);

    fin.close();
    return this->blockify();
}
// bool Matrix::load()
// {
//     logger.log("Matrix::load");
//     fstream fin(this->sourceFileName, ios::in);
//     string line;
//     if (getline(fin, line))
//     {
//         fin.close();
//         if (this->extractColumnNumbers(line))
//             if (this->blockify())
//                 return true;
//     }
//     fin.close();
//     return false;
// }
// bool Matrix::load()
// {

//     logger.log("Matrix::load");
//     cout << "LOAD1" << endl;
//     ifstream fin(this->sourceFileName, ios::in);
//     if (!fin.is_open())
//         return false;

//     string line, word;
//     vector<vector<int>> matrixData;

//     // Read the first row to determine matrix size
//     if (getline(fin, line))
//     {
//         stringstream s(line);
//         vector<int> firstRow;

//         while (getline(s, word, ','))
//         {
//             word.erase(std::remove_if(word.begin(), word.end(), ::isspace), word.end());
//             firstRow.push_back(stoi(word));
//         }

//         this->mat_size = firstRow.size();
//         // this->maxRowsPerBlock = (uint)((BLOCK_SIZE * 1000) / (sizeof(int) * this->mat_size));
//         this->maxRowsPerBlock = sqrt((BLOCK_SIZE * 1000) / sizeof(int));
//         this->maxColsPerBlock = this->maxRowsPerBlock;
//         this->blockLength = ceil((float)mat_size / maxColsPerBlock);

//         // Store first row as part of matrix data
//         matrixData.push_back(firstRow);
//     }
//     else
//     {
//         return false; // File was empty
//     }

//     // Read remaining rows
//     while (getline(fin, line))
//     {
//         stringstream s(line);
//         vector<int> row;

//         while (getline(s, word, ','))
//         {
//             word.erase(std::remove_if(word.begin(), word.end(), ::isspace), word.end());
//             row.push_back(stoi(word));
//         }

//         if (row.size() != this->mat_size)
//             return false; // Ensure all rows are of equal length (square matrix)

//         matrixData.push_back(row);
//     }

//     fin.close();
//     cout << "LOAD2" << endl;
//     // Call blockify to store matrix in pages
//     return this->blockify();
//     cout << "LOAD3" << endl;
// }

/**
 * @brief Function extracts column names from the header line of the .csv data
 * file.
 *
 * @param line
 * @return true if column names successfully extracted (i.e. no column name
 * repeats)
 * @return false otherwise
 */
// bool Matrix::extractColumnNumbers(string firstLine)
// {
//     logger.log("Matrix::extractColumnNumbers");
//     int columnNumbers = 0;
//     string word;
//     stringstream s(firstLine);
//     while (getline(s, word, ','))
//     {
//         word.erase(std::remove_if(word.begin(), word.end(), ::isspace), word.end());
//         columnNumbers++;
//     }
//     this->columnCount = columnNumbers;
//     this->maxRowsPerBlock = (uint)((BLOCK_SIZE * 1000) / (sizeof(int) * this->columnCount));
//     return true;
// }

/**
 * @brief This function splits all the rows and stores them in multiple files of
 * one block size.
 *
 * @return true if successfully blockified
 * @return false otherwise
 */
bool Matrix::blockify()
{
    logger.log("Matrix::blockify");
    ifstream fin(this->sourceFileName, ios::in);
    string line, word;

    // Fixed block size (15×15)
    this->maxRowsPerBlock = 15;
    this->maxColsPerBlock = 15;

    int numRowBlocks = ceil((float)this->mat_size / this->maxRowsPerBlock);
    int numColBlocks = ceil((float)this->mat_size / this->maxColsPerBlock);

    vector<vector<int>> matrixData(this->mat_size, vector<int>(this->mat_size));

    // Read entire matrix into memory (row-wise)
    for (int i = 0; i < this->mat_size; i++)
    {
        if (!getline(fin, line)) return false;
        stringstream s(line);
        for (int j = 0; j < this->mat_size; j++)
        {
            if (!getline(s, word, ',')) return false;
            matrixData[i][j] = stoi(word);
        }
    }
    fin.close();

    int blockID = 0;

    // Process the matrix in column-wise blocks
    for (int colBlock = 0; colBlock < numColBlocks; colBlock++)
    {
        for (int rowBlock = 0; rowBlock < numRowBlocks; rowBlock++)
        {
            int startRow = rowBlock * maxRowsPerBlock;
            int startCol = colBlock * maxColsPerBlock;
            int endRow = min(startRow + maxRowsPerBlock, this->mat_size);
            int endCol = min(startCol + maxColsPerBlock, this->mat_size);

            vector<vector<int>> block(endRow - startRow, vector<int>(endCol - startCol));

            for (int i = startRow; i < endRow; i++)
            {
                for (int j = startCol; j < endCol; j++)
                {
                    block[i - startRow][j - startCol] = matrixData[i][j];
                }
            }

            // Store the block as a page
            bufferManager.writePage(this->matrixName, blockID, block, endRow - startRow);
            this->blockCount++;
            this->rowsPerBlockCount.push_back(endRow - startRow);
            blockID++;
        }
    }
    return true;
}



// bool Matrix::blockify()
// {
//     logger.log("Matrix::blockify");
//     ifstream fin(this->sourceFileName, ios::in);
//     string line, word;

//     // Dynamically determine block size
//     // this->maxRowsPerBlock = sqrt((BLOCK_SIZE * 1000) / sizeof(int));
//     // this->maxColsPerBlock = this->maxRowsPerBlock;

//     int numRowBlocks = ceil((float)this->mat_size / this->maxRowsPerBlock);
//     int numColBlocks = ceil((float)this->mat_size / this->maxColsPerBlock);

//     int lastBlockRows = mat_size % maxRowsPerBlock;
//     int lastBlockCols = mat_size % maxColsPerBlock;

//     vector<vector<int>> matrixData(this->mat_size, vector<int>(this->mat_size));

//     // Read entire matrix into memory (row-wise)
//     for (int i = 0; i < this->mat_size; i++)
//     {
//         if (!getline(fin, line)) return false;
//         stringstream s(line);
//         for (int j = 0; j < this->mat_size; j++)
//         {
//             if (!getline(s, word, ',')) return false;
//             matrixData[i][j] = stoi(word);
//         }
//     }
//     fin.close();

//     int blockID = 0;

//     // Process the matrix in column-wise blocks
//     for (int colBlock = 0; colBlock < numColBlocks; colBlock++)
//     {
//         for (int rowBlock = 0; rowBlock < numRowBlocks; rowBlock++)
//         {
//             int startRow = rowBlock * maxRowsPerBlock;
//             int startCol = colBlock * maxColsPerBlock;
//             int endRow = min(startRow + maxRowsPerBlock, this->mat_size);
//             int endCol = min(startCol + maxColsPerBlock, this->mat_size);

//             vector<vector<int>> block(endRow - startRow, vector<int>(endCol - startCol));

//             for (int i = startRow; i < endRow; i++)
//             {
//                 for (int j = startCol; j < endCol; j++)
//                 {
//                     block[i - startRow][j - startCol] = matrixData[i][j];
//                 }
//             }

//             // Store the block as a page
//             bufferManager.writePage(this->matrixName, blockID, block, endRow - startRow);
//             this->blockCount++;
//             this->rowsPerBlockCount.push_back(endRow - startRow);
//             blockID++;
//         }
//     }
//     return true;
// }


// bool Matrix::blockify()
// {
//     cout << "BLOCKIFY1" << endl;
//     logger.log("Matrix::blockify");
//     ifstream fin(this->sourceFileName, ios::in);
//     string line, word;
//     vector<int> row(this->mat_size, 0);
//     vector<vector<int>> rowsInPage(this->maxRowsPerBlock, row);
//     int pageCounter = 0;
//     // unordered_set<int> dummy;
//     // dummy.clear();
//     // this->distinctValuesInColumns.assign(this->columnCount, dummy);
//     // this->distinctValuesPerColumnCount.assign(this->columnCount, 0);
//     // getline(fin, line);
//     while (getline(fin, line))
//     {
//         stringstream s(line);
//         for (int columnCounter = 0; columnCounter < this->mat_size; columnCounter++)
//         {
//             if (!getline(s, word, ','))
//                 return false;
//             row[columnCounter] = stoi(word);
//             rowsInPage[pageCounter][columnCounter] = row[columnCounter];
//         }
//         pageCounter++;
//         // this->updateStatistics(row);
//         if (pageCounter == this->maxRowsPerBlock)
//         {
//             cout << "BLOCKIFY2" << endl;
//             bufferManager.writePage(this->matrixName, this->blockCount, rowsInPage, pageCounter);
//             cout << "BLOCKIFY3" << endl;
//             this->blockCount++;
//             this->rowsPerBlockCount.emplace_back(pageCounter);
//             pageCounter = 0;
//         }
//     }
//     if (pageCounter)
//     {
//         cout << "BLOCKIFY4" << endl;
//         bufferManager.writePage(this->matrixName, this->blockCount, rowsInPage, pageCounter);
//         cout << "BLOCKIFY5" << endl;
//         this->blockCount++;
//         this->rowsPerBlockCount.emplace_back(pageCounter);
//         pageCounter = 0;
//     }

//     if (this->mat_size == 0)
//         return false;
//     // this->distinctValuesInColumns.clear();
//     return true;
// }

/**
 * @brief Given a row of values, this function will update the statistics it
 * stores i.e. it updates the number of rows that are present in the column and
 * the number of distinct values present in each column. These statistics are to
 * be used during optimisation.
 *
 * @param row
 */
// void Matrix::updateStatistics(vector<int> row)
// {
//     this->rowCount++;
//     for (int columnCounter = 0; columnCounter < this->columnCount; columnCounter++)
//     {
//         if (!this->distinctValuesInColumns[columnCounter].count(row[columnCounter]))
//         {
//             this->distinctValuesInColumns[columnCounter].insert(row[columnCounter]);
//             this->distinctValuesPerColumnCount[columnCounter]++;
//         }
//     }
// }

// Changes needed here
/**
 * @brief Function prints the first few rows of the table. If the table contains
 * more rows than PRINT_COUNT, exactly PRINT_COUNT rows are printed, else all
 * the rows are printed.
 *
 */
// void Matrix::print()
// {
//     logger.log("Matrix::print");
//     cout << "INSIDE MATRIX PRINT" << endl;
//     uint count = min(static_cast<uint>(PRINT_COUNT), this->mat_size);

//     // print headings
//     // this->writeRow(this->columns, cout);
//     cout << "HI1" << endl;
//     Cursor cursor(this->matrixName, 0);
//     cout << "HI2" << endl;
//     vector<int> row;
//     cout << "HI3" << endl;
//     for (int rowCounter = 0; rowCounter < count; rowCounter++)
//     {
//         row = cursor.getNext();
//         if (row.empty()) break;
//         this->writeRow(row, cout);
//     }
//     cout << "HI4" << endl;
//     printRowCount(this->mat_size);
//     cout << "HI5" << endl;
// }
void Matrix::print()
{
    logger.log("Matrix::print");
    cout << "INSIDE MATRIX PRINT" << endl;

    uint count = min(static_cast<uint>(PRINT_COUNT), this->mat_size);
    cout << "HI1" << endl;
    Cursor cursor(this->matrixName, 0);  // Now handles matrices correctly
    cout << "HI2" << endl;

    vector<int> row;
    cout << "HI3" << endl;
    
    for (int rowCounter = 0; rowCounter < count; rowCounter++) {
        row = cursor.getNext();
        if (row.empty()) break;
        this->writeRow(row, cout);
    }

    cout << "HI4" << endl;
    printRowCount(this->mat_size);
    cout << "HI5" << endl;
}

/**
 * @brief This function returns one row of the table using the cursor object. It
 * returns an empty row is all rows have been read.
 *
 * @param cursor
 * @return vector<int>
 */
void Matrix::getNextPage(Cursor *cursor)
{
    logger.log("Matrix::getNext");

    if (cursor->pageIndex < this->blockCount - 1)
    {
        cursor->nextPage(cursor->pageIndex + 1);
    }
}

/**
 * @brief called when EXPORT command is invoked to move source file to "data"
 * folder.
 *
 */
void Matrix::makePermanent()
{
    logger.log("Matrix::makePermanent");
    if (!this->isPermanent())
        bufferManager.deleteFile(this->sourceFileName);
    string newSourceFile = "../data/" + this->matrixName + ".csv";
    ofstream fout(newSourceFile, ios::out);

    // print headings
    // this->writeRow(this->columns, fout);

    Cursor cursor(this->matrixName, 0);
    vector<int> row;
    for (int rowCounter = 0; rowCounter < this->mat_size; rowCounter++)
    {
        row = cursor.getNext();
        this->writeRow(row, fout);
    }
    fout.close();
}

/**
 * @brief Function to check if table is already exported
 *
 * @return true if exported
 * @return false otherwise
 */
bool Matrix::isPermanent()
{
    logger.log("Matrix::isPermanent");
    if (this->sourceFileName == "../data/" + this->matrixName + ".csv")
        return true;
    return false;
}

/**
 * @brief The unload function removes the matrix from the database by deleting
 * all temporary files created as part of this matrix
 *
 */
void Matrix::unload()
{
    logger.log("Matrix::~unload");
    for (int pageCounter = 0; pageCounter < this->blockCount; pageCounter++)
        bufferManager.deleteFile(this->matrixName, pageCounter);
    if (!isPermanent())
        bufferManager.deleteFile(this->sourceFileName);
}

/**
 * @brief Function that returns a cursor that reads rows from this matrix
 *
 * @return Cursor
 */
Cursor Matrix::getCursor()
{
    logger.log("Matrix::getCursor");
    Cursor cursor(this->matrixName, 0);
    return cursor;
}

vector<vector<int>> Matrix::subMatrixTranspose(vector<vector<int>> subMatrix){
    logger.log("Matrix::subMatrixRotate");
    int numRows = subMatrix.size();
    int numCols = subMatrix[0].size();
    // cout<<"HERE";
    // if(numRows != numCols){
    //     vector<vector<int>> transposedSubMatrix(numCols, vector<int>(numRows));
    //     for(int row=0; row<numRows; row++){
    //         for(int col; col<numCols; col++){
    //             transposedSubMatrix[col][row] = subMatrix[row][col];
    //         }
    //     }
    //     return transposedSubMatrix;
    // }
    vector<vector<int>> transposedSubMatrix(numCols, vector<int>(numRows));
        for(int row=0; row<numRows; row++){
            for(int col=0; col<numCols; col++){
                transposedSubMatrix[col][row] = subMatrix[row][col];
            }
        }
        return transposedSubMatrix;
    return subMatrix;
}

void Matrix::rotate() {
    logger.log("Matrix::rotate");
    // cout<<"here";
    // cout<<this->blockLength;

    vector<vector<int>> subMatrix1, subMatrix2;
    bufferManager.clearBuffer();

    for (int pageRow = 0; pageRow < this->blockLength; pageRow++) {
        for (int pageCol = pageRow; pageCol < this->blockLength; pageCol++) {
            int newRow = pageCol;
            int newCol = this->blockLength - 1 - pageRow;

            if (pageRow == pageCol) {
                subMatrix1 = bufferManager.readPage(this->matrixName, pageRow*this->blockLength+pageCol);
                subMatrix1 = this->subMatrixTranspose(subMatrix1);
                for (auto &row : subMatrix1) {
                    reverse(row.begin(), row.end());
                }
                bufferManager.writePage(this->matrixName, newRow*this->blockLength+newCol, subMatrix1, subMatrix1.size());
                bufferManager.clearBuffer();
                continue;
            }
            subMatrix1 = bufferManager.readPage(this->matrixName, pageRow*this->blockLength+pageCol);
            subMatrix2 = bufferManager.readPage(this->matrixName, newRow*this->blockLength+newCol);

            subMatrix1 = this->subMatrixTranspose(subMatrix1);
            subMatrix2 = this->subMatrixTranspose(subMatrix2);

            for (auto &row : subMatrix1) {
                reverse(row.begin(), row.end());
            }
            for (auto &row : subMatrix2) {
                reverse(row.begin(), row.end());
            }
            bufferManager.writePage(this->matrixName, newRow*this->blockLength+newCol, subMatrix1, subMatrix1.size());
            bufferManager.writePage(this->matrixName, pageRow*this->blockLength+pageCol, subMatrix2, subMatrix2.size());
            bufferManager.clearBuffer();
        }
    }
}

void Matrix::crossTranspose(Matrix* matrix2) {
    logger.log("Matrix::crossTranspose");
    vector<vector<int>> subMatrix1, subMatrix2, subMatrix3, subMatrix4;
    bufferManager.clearBuffer();
    for(int pageRowCounter=0; pageRowCounter<this->blockLength; pageRowCounter++){
        for(int pageColCounter=pageRowCounter; pageColCounter<this->blockLength; pageColCounter++){
            if(pageRowCounter==pageColCounter){
                subMatrix1 = bufferManager.readPage(this->matrixName, pageRowCounter*this->blockLength+pageColCounter);
                subMatrix1 = this->subMatrixTranspose(subMatrix1);
                subMatrix2 = bufferManager.readPage(matrix2->matrixName, pageRowCounter*this->blockLength+pageColCounter);
                subMatrix2 = matrix2->subMatrixTranspose(subMatrix2);
                bufferManager.writePage(this->matrixName, pageColCounter*this->blockLength+pageRowCounter, subMatrix2, subMatrix2.size());
                bufferManager.writePage(matrix2->matrixName, pageColCounter*this->blockLength+pageRowCounter, subMatrix1, subMatrix1.size());
                bufferManager.clearBuffer();
                continue;
            }
            subMatrix1 = bufferManager.readPage(this->matrixName, pageRowCounter*this->blockLength+pageColCounter);
            subMatrix2 = bufferManager.readPage(this->matrixName, pageColCounter*this->blockLength+pageRowCounter);
            subMatrix1 = this->subMatrixTranspose(subMatrix1);
            subMatrix2 = this->subMatrixTranspose(subMatrix2);

            subMatrix3 = bufferManager.readPage(matrix2->matrixName, pageRowCounter*this->blockLength+pageColCounter);
            subMatrix4 = bufferManager.readPage(matrix2->matrixName, pageColCounter*this->blockLength+pageRowCounter);
            subMatrix3 = this->subMatrixTranspose(subMatrix3);
            subMatrix4 = this->subMatrixTranspose(subMatrix4);
            bufferManager.writePage(this->matrixName, pageColCounter*this->blockLength+pageRowCounter, subMatrix3, subMatrix3.size());
            bufferManager.writePage(this->matrixName, pageRowCounter*this->blockLength+pageColCounter, subMatrix4, subMatrix4.size());
            bufferManager.writePage(matrix2->matrixName, pageColCounter*this->blockLength+pageRowCounter, subMatrix1, subMatrix1.size());
            bufferManager.writePage(matrix2->matrixName, pageRowCounter*this->blockLength+pageColCounter, subMatrix2, subMatrix2.size());
            bufferManager.clearBuffer();
        }
    }
}

bool Matrix::checkSubMatrixAntiSym(vector<vector<int>>subMatrix1, vector<vector<int>>subMatrix2){
    logger.log("Matrix::checkSubMatrixAntiSym");
    // cout<<"HERE";
    int numRows = subMatrix1.size();
    int numCols = subMatrix1[0].size();
    subMatrix2 = this->subMatrixTranspose(subMatrix2);
    for(int row=0; row<numRows; row++){
        for(int col=0; col<numCols; col++){
            if(subMatrix1[row][col] != -(subMatrix2[row][col])){
                return false;
            }
        }
    }
    return true;
}

bool Matrix::checkAntiSym(){
    logger.log("Matrix::checkAntiSym");
    // cout<<"HERE";
    vector<vector<int>> subMatrix1, subMatrix2;
    bufferManager.clearBuffer();
    // cout<<"HERE";
    for(int pageRowCounter=0; pageRowCounter<this->blockLength; pageRowCounter++){
        for(int pageColCounter = pageRowCounter; pageColCounter<this->blockLength; pageColCounter++){
            if(pageRowCounter == pageColCounter){
                subMatrix1 = bufferManager.readPage(this->matrixName, pageRowCounter*this->blockLength+pageColCounter);
                if(this->checkSubMatrixAntiSym(subMatrix1, subMatrix1) == false){
                    bufferManager.clearBuffer();
                    return false;
                }
                bufferManager.clearBuffer();
                continue;
            }
            subMatrix1 = bufferManager.readPage(this->matrixName, pageRowCounter*this->blockLength+pageColCounter);
            subMatrix2 = bufferManager.readPage(this->matrixName, pageColCounter*this->blockLength+pageRowCounter);
            if(this->checkSubMatrixAntiSym(subMatrix1, subMatrix2) == false){
                bufferManager.clearBuffer();
                return false;
            }
            bufferManager.clearBuffer();
        }
    }
    return true;
}
