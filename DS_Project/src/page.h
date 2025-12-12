#include"logger.h"
/**
 * @brief The Page object is the main memory representation of a physical page
 * (equivalent to a block). The page class and the page.h header file are at the
 * bottom of the dependency tree when compiling files. 
 *<p>
 * Do NOT modify the Page class. If you find that modifications
 * are necessary, you may do so by posting the change you want to make on Moodle
 * or Teams with justification and gaining approval from the TAs. 
 *</p>
 */

class Page{

    string tableName;
    string pageIndex;
    int columnCount;
    int rowCount;
    vector<vector<int>> rows;
    bool isMatrix;
    public:

    string pageName = "";
    Page();
    Page(string tableName, int pageIndex);
    Page(string tableName, int pageIndex, vector<vector<int>> rows, int rowCount);
    vector<int> getRow(int rowIndex);
    vector<int> getMatrixRow(int rowIndex);
    void writePage();
    void writerow(vector<int> row, int rowcount);
    vector<vector<int>> readPage();
};
// class MatrixPage : public Page {
//     public:
//         MatrixPage();
//         MatrixPage(string matrixName, int pageIndex);
//         MatrixPage(string matrixName, int pageIndex, vector<vector<int>> block, int rowCount);
//         vector<int> getMatrixRow(int rowIndex);
//         void writePage() override;
//     };