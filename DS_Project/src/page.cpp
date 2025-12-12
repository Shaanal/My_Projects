#include "global.h"
/**
 * @brief Construct a new Page object. Never used as part of the code
 *
 */
Page::Page()
{
    this->pageName = "";
    this->tableName = "";
    this->pageIndex = -1;
    this->rowCount = 0;
    this->columnCount = 0;
    this->isMatrix = false;
    this->rows.clear();
}

/**
 * @brief Construct a new Page:: Page object given the table name and page
 * index. When tables are loaded they are broken up into blocks of BLOCK_SIZE
 * and each block is stored in a different file named
 * "<tablename>_Page<pageindex>". For example, If the Page being loaded is of
 * table "R" and the pageIndex is 2 then the file name is "R_Page2". The page
 * loads the rows (or tuples) into a vector of rows (where each row is a vector
 * of integers).
 *
 * @param tableName 
 * @param pageIndex 
 */
// Page::Page(string tableName, int pageIndex)
// {
//     logger.log("Page::Page");
//     this->tableName = tableName;
//     this->pageIndex = pageIndex;
//     this->pageName = "../data/temp/" + this->tableName + "_Page" + to_string(pageIndex);
//     Table table = *tableCatalogue.getTable(tableName);
//     this->columnCount = table.columnCount;
//     uint maxRowCount = table.maxRowsPerBlock;
//     vector<int> row(columnCount, 0);
//     this->rows.assign(maxRowCount, row);

//     ifstream fin(pageName, ios::in);
//     this->rowCount = table.rowsPerBlockCount[pageIndex];
//     int number;
//     for (uint rowCounter = 0; rowCounter < this->rowCount; rowCounter++)
//     {
//         for (int columnCounter = 0; columnCounter < columnCount; columnCounter++)
//         {
//             fin >> number;
//             this->rows[rowCounter][columnCounter] = number;
//         }
//     }
//     fin.close();
// }
Page::Page(string relationName, int pageIndex)
{
    logger.log("Page::Page");
    this->tableName = relationName;
    this->pageIndex = pageIndex;
    this->pageName = "../data/temp/" + this->tableName + "_Page" + to_string(pageIndex);

    if (matrixCatalogue.isMatrix(relationName)) {
        this->isMatrix = true;
        Matrix matrix = *matrixCatalogue.getMatrix(relationName);
        this->columnCount = matrix.mat_size;
        this->rowCount = matrix.rowsPerBlockCount[pageIndex];
    } else {
        this->isMatrix = false;
        Table table = *tableCatalogue.getTable(relationName);
        this->columnCount = table.columnCount;
        this->rowCount = table.rowsPerBlockCount[pageIndex];
    }

    vector<int> row(columnCount, 0);
    this->rows.assign(rowCount, row);

    ifstream fin(pageName, ios::in);
    int number;
    for (int rowCounter = 0; rowCounter < this->rowCount; rowCounter++) {
        for (int columnCounter = 0; columnCounter < columnCount; columnCounter++) {
            fin >> number;
            this->rows[rowCounter][columnCounter] = number;
        }
    }
    fin.close();
}
/**
 * @brief Get row from page indexed by rowIndex
 * 
 * @param rowIndex 
 * @return vector<int> 
 */
vector<int> Page::getRow(int rowIndex)
{
    logger.log("Page::getRow");
    vector<int> result;
    result.clear();
    if (rowIndex >= this->rowCount)
        return result;
    return this->rows[rowIndex];
}

vector<int> Page::getMatrixRow(int rowIndex)
{
    logger.log("Page::getMatrixRow");
    if (!this->isMatrix) {
        return {};
    }
    if (rowIndex >= this->rowCount)
        return {};
    return this->rows[rowIndex];
}

Page::Page(string tableName, int pageIndex, vector<vector<int>> rows, int rowCount)
{
    logger.log("Page::Page");
    this->tableName = tableName;
    this->pageIndex = pageIndex;
    this->rows = rows;
    this->rowCount = rowCount;
    this->columnCount = rows[0].size();
    this->isMatrix = matrixCatalogue.isMatrix(tableName);
    this->pageName = "../data/temp/"+this->tableName + "_Page" + to_string(pageIndex);
}

/**
 * @brief writes current page contents to file.
 * 
 */
// void Page::writePage()
// {
//     logger.log("Page::writePage");
//     ofstream fout(this->pageName, ios::trunc);
//     for (int rowCounter = 0; rowCounter < this->rowCount; rowCounter++)
//     {
//         for (int columnCounter = 0; columnCounter < this->columnCount; columnCounter++)
//         {
//             if (columnCounter != 0)
//                 fout << " ";
//             fout << this->rows[rowCounter][columnCounter];
//         }
//         fout << endl;
//     }
//     fout.close();
// }
void Page::writePage()
{
    logger.log("Page::writePage");
    ofstream fout(this->pageName, ios::trunc);

    // Check if the page belongs to a Matrix or a Table
    if (matrixCatalogue.isMatrix(this->tableName)) // If it's a matrix
    {
        logger.log("Page::writePage (Matrix)");
        for (int rowCounter = 0; rowCounter < this->rowCount; rowCounter++)
        {
            for (int columnCounter = 0; columnCounter < this->columnCount; columnCounter++)
            {
                if (columnCounter != 0)
                    fout << " ";
                fout << this->rows[rowCounter][columnCounter];
            }
            fout << endl;
        }
    }
    else // If it's a table (existing behavior)
    {
        logger.log("Page::writePage (Table)");
        for (int rowCounter = 0; rowCounter < this->rowCount; rowCounter++)
        {
            for (int columnCounter = 0; columnCounter < this->columnCount; columnCounter++)
            {
                if (columnCounter != 0)
                    fout << " ";
                fout << this->rows[rowCounter][columnCounter];
            }
            fout << endl;
        }
    }

    fout.close();
}

void Page::writerow(vector<int> row, int rowcount)
{
    logger.log("Page::writerow");
    ofstream fout(this->pageName, ios::app);
    if(rowcount == 1)
    {
        ofstream fout(this->pageName, ios::trunc);
    }
    // ofstream fout(this->pageName, ios::app);
    if (!fout.is_open()) {
        logger.log("Error: Could not open file " + this->pageName);
        return;
    }

    if (rowcount > this->rows.size()) {
        this->rows.resize(rowcount, vector<int>(this->columnCount, 0));
    }

    // Check if the page belongs to a Matrix or a Table
    if (matrixCatalogue.isMatrix(this->tableName)) // If it's a matrix
    {
        logger.log("Page::writerow (Matrix)");
        // for (int rowCounter = 0; rowCounter < this->rowCount; rowCounter++)
        // {
            for (int columnCounter = 0; columnCounter < this->columnCount; columnCounter++)
            {
                if (columnCounter != 0)
                    fout << " ";
                this->rows[rowcount-1][columnCounter] = row[columnCounter];
                fout << this->rows[rowcount-1][columnCounter];
            }
            fout << endl;
        this->rowCount = rowcount;
        // }
    }
    else // If it's a table (existing behavior)
    {
        logger.log("Page::writerow (Table)");
        // for (int rowCounter = 0; rowCounter < this->rowCount; rowCounter++)
        // {
            for (int columnCounter = 0; columnCounter < this->columnCount; columnCounter++)
            {
                if (columnCounter != 0)
                    fout << " ";
                this->rows[rowcount-1][columnCounter] = row[columnCounter];
                fout << this->rows[rowcount-1][columnCounter];
            }
            fout << endl;
        this->rowCount = rowcount;
        // cout << "Page::writerow: rowCount = " << this->rowCount << endl;
        // }
    }

    fout.close();
}

vector<vector<int>> Page::readPage()
{
    logger.log("Page::readPage");
    vector<vector<int>> rows;
    
    ifstream fin(this->pageName, ios::in);
    if (!fin)
    {
        logger.log("Error: Unable to open file " + this->pageName);
        return rows;
    }
    
    int number;
    while (!fin.eof())
    {
        vector<int> row;
        for (int i = 0; i < this->columnCount; i++)
        {
            if (fin >> number)
                row.push_back(number);
        }
        if (!row.empty())
            rows.push_back(row);
    }
    
    fin.close();
    return rows;
}
