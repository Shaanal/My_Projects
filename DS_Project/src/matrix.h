// #include "cursor.h"

// enum IndexingStrategy
// {
//     BTREE,
//     HASH,
//     NOTHING
// };

/**
 * @brief The Matrix class holds all information related to a loaded matrix. It
 * also implements methods that interact with the parsers, executors, cursors
 * and the buffer manager. There are typically 2 ways a matrix object gets
 * created through the course of the workflow - the first is by using the LOAD
 * command and the second is to use assignment statements (SELECT, PROJECT,
 * JOIN, SORT, CROSS and DISTINCT).
 *
 */

class Matrix
{
    // vector<unordered_set<int>> distinctValuesInColumns;

public:
    string sourceFileName = "";
    string matrixName = "";
    // vector<string> columns;
    // vector<uint> distinctValuesPerColumnCount;
    uint mat_size = 0;
    uint blockLength;
    // uint columnCount = 0; //
    // long long int rowCount = 0;             //
    uint blockCount = 0;
    uint maxRowsPerBlock = 0;
    uint maxColsPerBlock = 0;
    vector<uint> rowsPerBlockCount;
    bool indexed = false;
    // string indexedColumn = ""; //
    IndexingStrategy indexingStrategy = NOTHING;

    // bool extractColumnNumbers(string firstLine);
    bool blockify();
    // void updateStatistics(vector<int> row);
    Matrix();
    Matrix(string matrixName);
    // Matrix(string matrixName, vector<string> columns);
    bool load();
    // bool isColumn(string columnName);
    // void renameColumn(string fromColumnName, string toColumnName);
    void print();
    void makePermanent();
    bool isPermanent();
    void getNextPage(Cursor *cursor);
    Cursor getCursor();
    // int getColumnIndex(string columnName);
    void unload();
    void rotate();
    vector<vector<int>> subMatrixTranspose(vector<vector<int>> subMatrix);
    void crossTranspose(Matrix*);
    bool checkAntiSym();
    bool checkSubMatrixAntiSym(vector<vector<int>>, vector<vector<int>>);

    /**
     * @brief Static function that takes a vector of valued and prints them out in a
     * comma seperated format.
     *
     * @tparam T current usaages include int and string
     * @param row
     */
    template <typename T>
    void writeRow(vector<T> row, ostream &fout)
    {
        logger.log("Matrix::printRow");
        for (int columnCounter = 0; columnCounter < row.size(); columnCounter++)
        {
            if (columnCounter != 0)
                fout << ", ";
            fout << row[columnCounter];
        }
        fout << endl;
    }

    /**
     * @brief Static function that takes a vector of valued and prints them out in a
     * comma seperated format.
     *
     * @tparam T current usaages include int and string
     * @param row
     */
    template <typename T>
    void writeRow(vector<T> row)
    {
        logger.log("Matrix::printRow");
        ofstream fout(this->sourceFileName, ios::app);
        this->writeRow(row, fout);
        fout.close();
    }
};