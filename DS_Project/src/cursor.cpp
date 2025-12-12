#include "global.h"

// Cursor::Cursor(string tableName, int pageIndex)
// {
//     logger.log("Cursor::Cursor");
//     this->page = bufferManager.getPage(tableName, pageIndex);
//     this->pagePointer = 0;
//     this->tableName = tableName;
   
//     this->pageIndex = pageIndex;
// }
// Cursor::Cursor(string tableName, int pageIndex)
// {
//     logger.log("Cursor::Cursor");
//     this->page = bufferManager.getPage(tableName, pageIndex);
//     this->pagePointer = 0;
//     this->tableName = tableName;
//     if (matrixCatalogue.isMatrix(tableName)) {
//         this->isMatrix = true;
//     } else {
//         this->isMatrix = false;
//     }
//     this->pageIndex = pageIndex;
// }

/**
 * @brief This function reads the next row from the page. The index of the
 * current row read from the page is indicated by the pagePointer(points to row
 * in page the cursor is pointing to).
 *
 * @return vector<int> 
 */
// vector<int> Cursor::getNext()
// {
//     logger.log("Cursor::geNext");
//     vector<int> result = this->page.getRow(this->pagePointer);
//     this->pagePointer++;
//     if(result.empty()){
//         tableCatalogue.getTable(this->tableName)->getNextPage(this);
//         if(!this->pagePointer){
//             result = this->page.getRow(this->pagePointer);
//             this->pagePointer++;
//         }
//     }
//     return result;
// }
Cursor::Cursor(string relationName, int pageIndex)
{
    logger.log("Cursor::Cursor");

    this->tableName = relationName;
    this->pageIndex = pageIndex;
    this->pagePointer = 0;

    // Detect if relation is a Matrix
    if (matrixCatalogue.isMatrix(relationName)) {
        this->isMatrix = true;
    } else {
        this->isMatrix = false;
    }

    this->page = bufferManager.getPage(relationName, pageIndex);
}

/**
 * @brief Reads the next row from the page, handling both tables and matrices.
 */
vector<int> Cursor::getNext()
{
    logger.log("Cursor::getNext");

    if (this->isMatrix) {
        vector<int> result = this->page.getMatrixRow(this->pagePointer);
        this->pagePointer++;

        // Load next page if needed
        if (result.empty()) {
            matrixCatalogue.getMatrix(this->tableName)->getNextPage(this);
            if (!this->pagePointer) {
                result = this->page.getMatrixRow(this->pagePointer);
                this->pagePointer++;
            }
        }
        return result;
    }

    // Default: Table rows
    vector<int> result = this->page.getRow(this->pagePointer);
    this->pagePointer++;

    if (result.empty()) {
        tableCatalogue.getTable(this->tableName)->getNextPage(this);
        if (!this->pagePointer) {
            result = this->page.getRow(this->pagePointer);
            this->pagePointer++;
        }
    }
    return result;
}

/**
 * @brief Function that loads Page indicated by pageIndex. Now the cursor starts
 * reading from the new page.
 *
 * @param pageIndex 
 */
void Cursor::nextPage(int pageIndex)
{
    logger.log("Cursor::nextPage");
    this->page = bufferManager.getPage(this->tableName, pageIndex);
    this->pageIndex = pageIndex;
    this->pagePointer = 0;
}

/**
 * @brief Reads the next row from the page, handling both tables and matrices.
 */
vector<vector<int>> Cursor::getNextpage()
{
    logger.log("Cursor::getNextPage");

    // this->nextPage(pageIndex);

    vector<vector<int>> result;
    int rowcount = tableCatalogue.getTable(this->tableName)->rowsPerBlockCount[this->pageIndex];

    for (int i = 0; i < rowcount; i++) {
        result.push_back(this->page.getRow(i));
    }
    // for(int i=0;i<result.size();i++){
    //     for(int j=0;j<result[0].size();j++){
    //         cout<<result[i][j]<<" ";
    //     }
    //     cout<<endl;
    // }
    // Page p = bufferManager.getPage(this->tableName, this->pageIndex);
    // result = p.readPage();
    // cout <<"**"<< result.size() << endl;
    return result;
}
