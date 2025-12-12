#include "global.h"
const string LSM_INDEX_PATH = "../data/temp/";

class LSMTreeIndex {
private:
    string tableName;
    string columnName;
    int columnIndex;
    string indexFilePath;
    map<int, vector<int>> memtable;
    vector<string> sstableFiles;
    int sstableCounter = 0;
    const int MEMTABLE_LIMIT = 1000;
    void flushToDisk();

public:
    LSMTreeIndex(string tableName, string columnName);
    vector<vector<int>> search(int key);
    vector<vector<int>>  rangeSearch(string op, int value);
    vector<int> rangeSearchIndex(string op, int value);

    void insert(vector<string> keys, vector<int> values);

    void update(vector<int> idxs, string col, int val);

    void remove(vector<int> idxs);
};