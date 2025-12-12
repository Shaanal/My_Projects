#include "global.h"

/**
 * @brief Construct a new Table:: Table object
 *
 */
Table::Table()
{
    logger.log("Table::Table");
}

/**
 * @brief Construct a new Table:: Table object used in the case where the data
 * file is available and LOAD command has been called. This command should be
 * followed by calling the load function;
 *
 * @param tableName 
 */
Table::Table(string tableName)
{
    logger.log("Table::Table");
    this->sourceFileName = "../data/" + tableName + ".csv";
    this->tableName = tableName;
}

/**
 * @brief Construct a new Table:: Table object used when an assignment command
 * is encountered. To create the table object both the table name and the
 * columns the table holds should be specified.
 *
 * @param tableName 
 * @param columns 
 */
Table::Table(string tableName, vector<string> columns)
{
    logger.log("Table::Table");
    this->sourceFileName = "../data/temp/" + tableName + ".csv";
    this->tableName = tableName;
    this->columns = columns;
    this->columnCount = columns.size();
    this->maxRowsPerBlock = (uint)((BLOCK_SIZE * 1000) / (sizeof(int) * columnCount));
    this->writeRow<string>(columns);
}


/**
 * @brief The load function is used when the LOAD command is encountered. It
 * reads data from the source file, splits it into blocks and updates table
 * statistics.
 *
 * @return true if the table has been successfully loaded 
 * @return false if an error occurred 
 */
bool Table::load()
{
    logger.log("Table::load");
    fstream fin(this->sourceFileName, ios::in);
    string line;
    if (getline(fin, line))
    {
        fin.close();
        if (this->extractColumnNames(line))
            if (this->blockify())
                return true;
    }
    fin.close();
    return false;
}

/**
 * @brief Function extracts column names from the header line of the .csv data
 * file. 
 *
 * @param line 
 * @return true if column names successfully extracted (i.e. no column name
 * repeats)
 * @return false otherwise
 */
bool Table::extractColumnNames(string firstLine)
{
    logger.log("Table::extractColumnNames");
    unordered_set<string> columnNames;
    string word;
    stringstream s(firstLine);
    while (getline(s, word, ','))
    {
        word.erase(std::remove_if(word.begin(), word.end(), ::isspace), word.end());
        if (columnNames.count(word))
            return false;
        columnNames.insert(word);
        this->columns.emplace_back(word);
    }
    this->columnCount = this->columns.size();
    this->maxRowsPerBlock = (uint)((BLOCK_SIZE * 1000) / (sizeof(int) * this->columnCount));
    return true;
}

/**
 * @brief This function splits all the rows and stores them in multiple files of
 * one block size. 
 *
 * @return true if successfully blockified
 * @return false otherwise
 */
bool Table::blockify()
{
    logger.log("Table::blockify");
    ifstream fin(this->sourceFileName, ios::in);
    string line, word;
    vector<int> row(this->columnCount, 0);
    vector<vector<int>> rowsInPage(this->maxRowsPerBlock, row);
    int pageCounter = 0;
    unordered_set<int> dummy;
    dummy.clear();
    this->distinctValuesInColumns.assign(this->columnCount, dummy);
    this->distinctValuesPerColumnCount.assign(this->columnCount, 0);
    getline(fin, line);
    while (getline(fin, line))
    {
        stringstream s(line);
        for (int columnCounter = 0; columnCounter < this->columnCount; columnCounter++)
        {
            if (!getline(s, word, ','))
                return false;
            row[columnCounter] = stoi(word);
            rowsInPage[pageCounter][columnCounter] = row[columnCounter];
        }
        pageCounter++;
        this->updateStatistics(row);
        if (pageCounter == this->maxRowsPerBlock)
        {
            bufferManager.writePage(this->tableName, this->blockCount, rowsInPage, pageCounter);
            this->blockCount++;
            this->rowsPerBlockCount.emplace_back(pageCounter);
            pageCounter = 0;
        }
    }
    if (pageCounter)
    {
        bufferManager.writePage(this->tableName, this->blockCount, rowsInPage, pageCounter);
        this->blockCount++;
        this->rowsPerBlockCount.emplace_back(pageCounter);
        pageCounter = 0;
    }

    if (this->rowCount == 0)
        return false;
    this->distinctValuesInColumns.clear();
    return true;
}

/**
 * @brief Given a row of values, this function will update the statistics it
 * stores i.e. it updates the number of rows that are present in the column and
 * the number of distinct values present in each column. These statistics are to
 * be used during optimisation.
 *
 * @param row 
 */
void Table::updateStatistics(vector<int> row)
{
    this->rowCount++;
    for (int columnCounter = 0; columnCounter < this->columnCount; columnCounter++)
    {
        if (!this->distinctValuesInColumns[columnCounter].count(row[columnCounter]))
        {
            this->distinctValuesInColumns[columnCounter].insert(row[columnCounter]);
            this->distinctValuesPerColumnCount[columnCounter]++;
        }
    }
}

/**
 * @brief Checks if the given column is present in this table.
 *
 * @param columnName 
 * @return true 
 * @return false 
 */
bool Table::isColumn(string columnName)
{
    logger.log("Table::isColumn");
    for (auto col : this->columns)
    {
        if (col == columnName)
        {
            return true;
        }
    }
    return false;
}

/**
 * @brief Renames the column indicated by fromColumnName to toColumnName. It is
 * assumed that checks such as the existence of fromColumnName and the non prior
 * existence of toColumnName are done.
 *
 * @param fromColumnName 
 * @param toColumnName 
 */
void Table::renameColumn(string fromColumnName, string toColumnName)
{
    logger.log("Table::renameColumn");
    for (int columnCounter = 0; columnCounter < this->columnCount; columnCounter++)
    {
        if (columns[columnCounter] == fromColumnName)
        {
            columns[columnCounter] = toColumnName;
            break;
        }
    }
    return;
}

/**
 * @brief Function prints the first few rows of the table. If the table contains
 * more rows than PRINT_COUNT, exactly PRINT_COUNT rows are printed, else all
 * the rows are printed.
 *
 */
void Table::print()
{
    logger.log("Table::print");
    uint count = min((long long)PRINT_COUNT, this->rowCount);

    //print headings
    this->writeRow(this->columns, cout);

    Cursor cursor(this->tableName, 0);
    vector<int> row;
    for (int rowCounter = 0; rowCounter < count; rowCounter++)
    {
        row = cursor.getNext();
        this->writeRow(row, cout);
    }
    printRowCount(this->rowCount);
}



/**
 * @brief This function returns one row of the table using the cursor object. It
 * returns an empty row is all rows have been read.
 *
 * @param cursor 
 * @return vector<int> 
 */
void Table::getNextPage(Cursor *cursor)
{
    logger.log("Table::getNext");

        if (cursor->pageIndex < this->blockCount - 1)
        {
            cursor->nextPage(cursor->pageIndex+1);
        }
}



/**
 * @brief called when EXPORT command is invoked to move source file to "data"
 * folder.
 *
 */
void Table::makePermanent()
{
    logger.log("Table::makePermanent");
    if(!this->isPermanent())
        bufferManager.deleteFile(this->sourceFileName);
    string newSourceFile = "../data/" + this->tableName + ".csv";
    ofstream fout(newSourceFile, ios::out);

    //print headings
    this->writeRow(this->columns, fout);

    Cursor cursor(this->tableName, 0);
    vector<int> row;
    for (int rowCounter = 0; rowCounter < this->rowCount; rowCounter++)
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
bool Table::isPermanent()
{
    logger.log("Table::isPermanent");
    if (this->sourceFileName == "../data/" + this->tableName + ".csv")
    return true;
    return false;
}

/**
 * @brief The unload function removes the table from the database by deleting
 * all temporary files created as part of this table
 *
 */
void Table::unload(){
    logger.log("Table::~unload");
    for (int pageCounter = 0; pageCounter < this->blockCount; pageCounter++)
        bufferManager.deleteFile(this->tableName, pageCounter);
    if (!isPermanent())
        bufferManager.deleteFile(this->sourceFileName);
}

/**
 * @brief Function that returns a cursor that reads rows from this table
 * 
 * @return Cursor 
 */
Cursor Table::getCursor()
{
    logger.log("Table::getCursor");
    Cursor cursor(this->tableName, 0);
    return cursor;
}
/**
 * @brief Function that returns the index of column indicated by columnName
 * 
 * @param columnName 
 * @return int 
 */
int Table::getColumnIndex(string columnName)
{
    logger.log("Table::getColumnIndex");
    for (int columnCounter = 0; columnCounter < this->columnCount; columnCounter++)
    {
        if (this->columns[columnCounter] == columnName)
            return columnCounter;
    }
    return -1;
}

const int MAX_PAGES_IN_MEMORY = 10;
const int PRIME_HASH_MOD = 103;

int hashFunction(int key) {
    return abs(key) % PRIME_HASH_MOD;
}

// Two-Pass Hash Join with disk-based storage
void Table::hashJoin(string table2, string col1, string col2, string restable)
{
    // Table* leftTable = tableCatalogue.getTable(table1);
    Table* rightTable = tableCatalogue.getTable(table2);
    
    int col1Index = this->getColumnIndex(col1);
    int col2Index = rightTable->getColumnIndex(col2);
    
    vector<string> resultColumns = this->columns;
    resultColumns.insert(resultColumns.end(), rightTable->columns.begin(), rightTable->columns.end());
    Table* resultTable = new Table(restable, resultColumns);
    tableCatalogue.insertTable(resultTable);
    
    Table* leftPartitionTable = new Table("leftPartitionTable", this->columns);
    Table* rightPartitionTable = new Table("rightPartitionTable", rightTable->columns);
    tableCatalogue.insertTable(leftPartitionTable);
    tableCatalogue.insertTable(rightPartitionTable);
    
    unordered_map<int, int> leftPartitionIndices;
    unordered_map<int, int> rightPartitionIndices;
    
    vector<vector<vector<int>>> leftPartitions(PRIME_HASH_MOD);
    vector<vector<vector<int>>> rightPartitions(PRIME_HASH_MOD);
    
    Cursor leftCursor = this->getCursor();
    Cursor rightCursor = rightTable->getCursor();
    vector<int> row;
    
    cout << "Partitioning left table..." << endl;
    while (!(row = leftCursor.getNext()).empty()) {
        int key = row[col1Index];
        int partitionIndex = hashFunction(key);
        leftPartitions[partitionIndex].push_back(row);
    }
    
    cout << "Partitioning right table..." << endl;
    while (!(row = rightCursor.getNext()).empty()) {
        int key = row[col2Index];
        int partitionIndex = hashFunction(key);
        rightPartitions[partitionIndex].push_back(row);
    }
    
    cout << "Writing partitions to disk..." << endl;
    for (int i = 0; i < PRIME_HASH_MOD; i++) {
        if (!leftPartitions[i].empty()) {
            bufferManager.writePage(leftPartitionTable->tableName, i-1, leftPartitions[i], leftPartitions[i].size());
            leftPartitionTable->rowsPerBlockCount.emplace_back(leftPartitions[i].size());
            leftPartitionTable->rowCount += leftPartitions[i].size();
            leftPartitionTable->blockCount++;
        }
        if (!rightPartitions[i].empty()) {
            bufferManager.writePage(rightPartitionTable->tableName, i-1, rightPartitions[i], rightPartitions[i].size());
            rightPartitionTable->rowsPerBlockCount.emplace_back(rightPartitions[i].size());
            rightPartitionTable->rowCount += rightPartitions[i].size();
            rightPartitionTable->blockCount++;
        }
    }

    // leftPartitionTable->blockCount = leftPartitionTable->rowsPerBlockCount.size();
    // rightPartitionTable->blockCount = rightPartitionTable->rowsPerBlockCount.size();
    
    vector<vector<int>> resultBuffer;
    int pageIndex = 0;
    
    cout << "Starting join phase..." << endl;
    int maxPartitions = max(leftPartitionTable->blockCount, rightPartitionTable->blockCount);
    // cout<<maxPartitions<<endl;
    for (int i = 0; i < maxPartitions; i++) {

        unordered_map<int, vector<vector<int>>> hashTable;

        // Load left partition if available
        vector<vector<int>> leftPartition;
        if (i <= leftPartitionTable->blockCount) {
            leftPartition = bufferManager.readPage(leftPartitionTable->tableName, i);
            for (auto& row : leftPartition) {
                int key = row[col1Index];
                hashTable[key].push_back(row);
            }
        }

        // Load right partition if available
        vector<vector<int>> rightPartition;
        if (i <= rightPartitionTable->blockCount) {
            // cout<<"RightPartition: "<<i<<endl;
            rightPartition = bufferManager.readPage(rightPartitionTable->tableName, i);
            for (auto& row : rightPartition) {
                int key = row[col2Index];
                if (hashTable.find(key) != hashTable.end()) {
                    for (const auto& leftRow : hashTable[key]) {
                        vector<int> joinedRow = leftRow;
                        joinedRow.insert(joinedRow.end(), row.begin(), row.end());
                        resultBuffer.push_back(joinedRow);

                        if (resultBuffer.size() >= resultTable->maxRowsPerBlock) {
                            bufferManager.writePage(resultTable->tableName, pageIndex++, resultBuffer, resultBuffer.size());
                            resultTable->rowsPerBlockCount.emplace_back(resultBuffer.size());
                            resultTable->rowCount += resultBuffer.size();
                            resultTable->blockCount++;
                            resultBuffer.clear();
                        }
                    }
                }
            }
        }
    }
    
    if (!resultBuffer.empty()) {
        bufferManager.writePage(resultTable->tableName, pageIndex++, resultBuffer, resultBuffer.size());
        resultTable->rowsPerBlockCount.emplace_back(resultBuffer.size());
        resultTable->rowCount += resultBuffer.size();
        resultTable->blockCount++;
    }
    // cout<<"here"<<endl;
    if (resultTable->rowCount == 0) {  
        // Create a row with all columns set to -1 for empty table
        vector<int> emptyRow(resultTable->columns.size(), -1);
        vector<vector<int>> emptyPage = {emptyRow};

        // Write the empty row to disk
        bufferManager.writePage(resultTable->tableName, 0, emptyPage, 1);
        resultTable->rowsPerBlockCount.push_back(1);
        resultTable->rowCount = 1;
        resultTable->blockCount = 1;
    }
    // resultTable->sortTable(col1Index);
    
    cout << "JOIN OPERATION COMPLETED SUCCESSFULLY"<<endl;
}

vector<int> Table::getRow(int idx){
    logger.log("Table::getRow");
    int pageNo = int(idx/this->maxRowsPerBlock);
    int rowNo = idx%this->maxRowsPerBlock;

    vector<vector<int>> page;
    page = bufferManager.readPage(this->tableName, pageNo);
    vector<int> row = page[rowNo];
    return row;
}

void Table::insertRow(vector<int> newRow){
    logger.log("Table::insertRow");
    int pageNo = this->blockCount;
    // cout<<pageNo<<endl;
    vector<vector<int>> page;
    page = bufferManager.readPage(this->tableName, pageNo-1);
    if(page.size() >= maxRowsPerBlock){
        vector<vector<int>> newPage;
        newPage.push_back(newRow);
        bufferManager.writePage(this->tableName, pageNo, newPage, newPage.size());
        this->rowsPerBlockCount.emplace_back(newPage.size());
        this->rowCount += newPage.size();
        this->blockCount++;
    }
    else{
        page.emplace_back(newRow);
        bufferManager.writePage(this->tableName, pageNo-1, page, page.size());
        this->rowsPerBlockCount[pageNo-1] = page.size();
        this->rowCount += 1;
    }
}

void Table::updateRow(int idx, string key, int value){
    logger.log("Table::updateRow");
    int pageNo = int(idx/this->maxRowsPerBlock);
    int rowNo = idx%this->maxRowsPerBlock;

    vector<vector<int>> page;
    page = bufferManager.readPage(this->tableName, pageNo);
    vector<int> row = page[rowNo];
    auto it = std::find(this->columns.begin(), this->columns.end(), key);
    int index = std::distance(this->columns.begin(), it);
    row[index] = value;
    page[rowNo] = row;
    bufferManager.writePage(this->tableName, pageNo, page, page.size());
}

void Table::deleteRow(int idx){
    logger.log("Table::deleteRow");
    int pageNo = int(idx/this->maxRowsPerBlock);
    int rowNo = idx%this->maxRowsPerBlock;

    vector<vector<int>> page, newPage;
    page = bufferManager.readPage(this->tableName, pageNo);
    page.erase(page.begin() + rowNo);
    bufferManager.writePage(this->tableName, pageNo, page, page.size());
    this->rowsPerBlockCount[pageNo] = page.size();
    this->rowCount -= 1;
}
