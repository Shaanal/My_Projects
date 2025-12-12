#include "lsmIndex.h"

// const string LSM_INDEX_PATH = "../data/temp/";

void printVector(const std::vector<int>& vec) {
    for (int i = 0; i < vec.size(); ++i) {
        std::cout << vec[i];
        if (i < vec.size() - 1)
            std::cout << " ";
    }
    std::cout << std::endl;
}

void printVector(const std::vector<string>& vec) {
    for (int i = 0; i < vec.size(); ++i) {
        std::cout << vec[i];
        if (i < vec.size() - 1)
            std::cout << " ";
    }
    std::cout << std::endl;
}

vector<int> getOrderedValues(const std::vector<std::string>& keys,
                                  const std::vector<int>& values,
                                  const std::vector<std::string>& columns) {
    std::unordered_map<std::string, int> keyValueMap;
    
    // Fill the map with keys and their corresponding values
    for (size_t i = 0; i < keys.size(); ++i) {
        keyValueMap[keys[i]] = values[i];
    }
    
    std::vector<int> orderedValues;
    
    // For each column, get the value from the map, or 0 if not found
    for (const auto& col : columns) {
        if (keyValueMap.find(col) != keyValueMap.end()) {
            orderedValues.push_back(keyValueMap[col]);
        } else {
            orderedValues.push_back(0);
        }
    }
    
    return orderedValues;
}

LSMTreeIndex::LSMTreeIndex(string tableName, string columnName)
    : tableName(tableName), columnName(columnName), sstableCounter(0) {

    Table* table = tableCatalogue.getTable(tableName);
    if (!table) {
        cerr << "Table not found!" << endl;
        return;
    }

    columnIndex = table->getColumnIndex(columnName);
    if (columnIndex == -1) {
        cerr << columnName << "Column not found!" << endl;
        return;
    }

    Cursor cursor = table->getCursor();
    vector<int> row;
    int rowIndex = 0;

    while (!(row = cursor.getNext()).empty()) {
        int key = row[columnIndex];
        memtable[key].push_back(rowIndex++);
        if (memtable.size() >= MEMTABLE_LIMIT) {
            flushToDisk();
        }
    }

    if (!memtable.empty()) {
        flushToDisk();
    }

    cout << "LSM Tree index created for " << tableName << "." << columnName << "." << endl;
}

void LSMTreeIndex::flushToDisk() {
    string filename = LSM_INDEX_PATH + tableName + "_" + columnName + "_sstable_" + to_string(sstableCounter++) + ".txt";
    ofstream outFile(filename);
    for (auto &entry : memtable) {
        outFile << entry.first;
        for (int rowIdx : entry.second)
            outFile << "," << rowIdx;
        outFile << "\n";
    }
    outFile.close();
    sstableFiles.push_back(filename);
    memtable.clear();
}

vector<vector<int>> LSMTreeIndex::search(int key) {
    vector<int> rowIndices;
    if (memtable.find(key) != memtable.end()) {
        rowIndices.insert(rowIndices.end(), memtable[key].begin(), memtable[key].end());
    }

    for (auto &file : sstableFiles) {
        ifstream inFile(file);
        string line;
        while (getline(inFile, line)) {
            stringstream ss(line);
            string token;
            getline(ss, token, ',');
            int fileKey = stoi(token);
            if (fileKey == key) {
                while (getline(ss, token, ',')) {
                    rowIndices.push_back(stoi(token));
                }
                break;
            }
        }
        inFile.close();
    }

    vector<vector<int>> resultRows;
    Table* table = tableCatalogue.getTable(tableName);
    if (table) {
        for (int idx : rowIndices) {
            resultRows.push_back(table->getRow(idx));
        }
    }

    return resultRows;
}

vector<vector<int>> LSMTreeIndex::rangeSearch(string op, int value) {
    vector<int> rowIndices;

    for (auto& [key, rows] : memtable) {
        if ((op == ">" && key > value) || (op == "<" && key < value) ||
            (op == "=" && key == value) || (op == ">=" && key >= value) ||
            (op == "<=" && key <= value) || (op == "!=" && key != value)) {
            rowIndices.insert(rowIndices.end(), rows.begin(), rows.end());
        }
    }

    for (auto& file : sstableFiles) {
        ifstream inFile(file);
        string line;
        while (getline(inFile, line)) {
            stringstream ss(line);
            string token;
            getline(ss, token, ',');
            int key = stoi(token);
            if ((op == ">" && key > value) || (op == "<" && key < value) ||
                (op == "=" && key == value) || (op == ">=" && key >= value) ||
                (op == "<=" && key <= value) || (op == "!=" && key != value)) {
                while (getline(ss, token, ',')) {
                    rowIndices.push_back(stoi(token));
                }
            }
        }
        inFile.close();
    }

    vector<vector<int>> resultRows;
    Table* table = tableCatalogue.getTable(tableName);
    if (table) {
        // printVector(table->columns);
        for (int idx : rowIndices) {
            resultRows.push_back(table->getRow(idx));
            // printVector(table->getRow(idx));
        }
    }
    return resultRows;
}

vector<int> LSMTreeIndex::rangeSearchIndex(string op, int value) {
    vector<int> rowIndices;

    for (auto& [key, rows] : memtable) {
        if ((op == ">" && key > value) || (op == "<" && key < value) ||
            (op == "=" && key == value) || (op == ">=" && key >= value) ||
            (op == "<=" && key <= value) || (op == "!=" && key != value)) {
            rowIndices.insert(rowIndices.end(), rows.begin(), rows.end());
        }
    }

    for (auto& file : sstableFiles) {
        ifstream inFile(file);
        string line;
        while (getline(inFile, line)) {
            stringstream ss(line);
            string token;
            getline(ss, token, ',');
            int key = stoi(token);
            if ((op == ">" && key > value) || (op == "<" && key < value) ||
                (op == "=" && key == value) || (op == ">=" && key >= value) ||
                (op == "<=" && key <= value) || (op == "!=" && key != value)) {
                while (getline(ss, token, ',')) {
                    rowIndices.push_back(stoi(token));
                }
            }
        }
        inFile.close();
    }

    return rowIndices;
}

void LSMTreeIndex::insert(vector<string> keys, vector<int> values) {
    // memtable[key].push_back(rowIndex);
    // if (memtable.size() >= MEMTABLE_LIMIT) {
    //     flushToDisk();
    // }
    // printVector(keys);
    // printVector(values);

    Table* table = tableCatalogue.getTable(tableName);
    if (table) {
        std::vector<int> result = getOrderedValues(keys, values,table->columns);
        // printVector(result);
        table->insertRow(result);
    }
}

void LSMTreeIndex::update(vector<int> idxs, string col, int val) {
    Table* table = tableCatalogue.getTable(tableName);
    if (table) {
        // vector<int> row = table->getRow(rowIndex);
        for (size_t i = 0; i < idxs.size(); ++i) {
            table->updateRow(idxs[i], col, val);
        }
    }
}

void LSMTreeIndex::remove(vector<int> idxs) {
    // auto it = memtable.find(key);
    // if (it != memtable.end()) {
    //     auto& vec = it->second;
    //     // vec.erase(remove(vec.begin(), vec.end(), rowIndex), vec.end());
    //     if (vec.empty()) {
    //         memtable.erase(it);
    //     }
    // }

    Table* table = tableCatalogue.getTable(tableName);
    if (table) {
        // vector<int> row = table->getRow(rowIndex);
        for (size_t i = 0; i < idxs.size(); ++i) {
            table->deleteRow(idxs[i]);
        }
    }
    // if (table) {
    //     table->deleteRow(rowIndex);
    // }
}

// #include "global.h"

// const string LSM_INDEX_PATH = "../data/temp/";

// void printVector(const std::vector<int>& vec) {
//     for (int i = 0; i < vec.size(); ++i) {
//         std::cout << vec[i];
//         if (i < vec.size() - 1)
//             std::cout << " ";
//     }
//     std::cout << std::endl;
// }

// void printVector(const std::vector<string>& vec) {
//     for (int i = 0; i < vec.size(); ++i) {
//         std::cout << vec[i];
//         if (i < vec.size() - 1)
//             std::cout << " ";
//     }
//     std::cout << std::endl;
// }

// class LSMTreeIndex {
// private:
//     string tableName;
//     string columnName;
//     int columnIndex;
//     string indexFilePath;
//     map<int, vector<int>> memtable;
//     vector<string> sstableFiles;
//     int sstableCounter = 0;
//     const int MEMTABLE_LIMIT = 1000;

//     void flushToDisk() {
//         string filename = LSM_INDEX_PATH + tableName + "_" + columnName + "_sstable_" + to_string(sstableCounter++) + ".txt";
//         ofstream outFile(filename);
//         for (auto &entry : memtable) {
//             outFile << entry.first;
//             for (int rowIdx : entry.second)
//                 outFile << "," << rowIdx;
//             outFile << "\n";
//         }
//         outFile.close();
//         sstableFiles.push_back(filename);
//         memtable.clear();
//     }

// public:
//     LSMTreeIndex(string tableName, string columnName) : tableName(tableName), columnName(columnName) {
//         Table* table = tableCatalogue.getTable(tableName);
//         if (!table) {
//             cerr << "Table not found!" << endl;
//             return;
//         }
//         columnIndex = table->getColumnIndex(columnName);
//         if (columnIndex == -1) {
//             cerr << "Column not found!" << endl;
//             return;
//         }

//         Cursor cursor = table->getCursor();
//         vector<int> row;
//         int rowIndex = 0;

//         while (!(row = cursor.getNext()).empty()) {
//             int key = row[columnIndex];
//             memtable[key].push_back(rowIndex++);
//             if (memtable.size() >= MEMTABLE_LIMIT) {
//                 flushToDisk();
//             }
//         }
//         if (!memtable.empty()) {
//             flushToDisk();
//         }

//         cout << "LSM Tree index created for " << tableName << "." << columnName << "." << endl;
//     }

//     vector<vector<int>> search(int key) {
//         vector<int> rowIndices;
//         if (memtable.find(key) != memtable.end()) {
//             rowIndices.insert(rowIndices.end(), memtable[key].begin(), memtable[key].end());
//         }
//         for (auto &file : sstableFiles) {
//             ifstream inFile(file);
//             string line;
//             while (getline(inFile, line)) {
//                 stringstream ss(line);
//                 string token;
//                 getline(ss, token, ',');
//                 int fileKey = stoi(token);
//                 if (fileKey == key) {
//                     while (getline(ss, token, ',')) {
//                         rowIndices.push_back(stoi(token));
//                     }
//                     break;
//                 }
//             }
//             inFile.close();
//         }

//         vector<vector<int>> resultRows;
//         Table* table = tableCatalogue.getTable(tableName);
//         if (table) {
//             for (int idx : rowIndices) {
//                 resultRows.push_back(table->getRow(idx));
//             }
//         }

//         return resultRows;
//     }

//     void rangeSearch(string op, int value) {
//         vector<int> rowIndices;

//         for (auto& [key, rows] : memtable) {
//             if ((op == ">" && key > value) || (op == "<" && key < value) ||
//                 (op == "=" && key == value) || (op == ">=" && key >= value) ||
//                 (op == "<=" && key <= value) || (op == "!=" && key != value)) {
//                 rowIndices.insert(rowIndices.end(), rows.begin(), rows.end());
//             }
//         }

//         for (auto& file : sstableFiles) {
//             ifstream inFile(file);
//             string line;
//             while (getline(inFile, line)) {
//                 stringstream ss(line);
//                 string token;
//                 getline(ss, token, ',');
//                 int key = stoi(token);
//                 if ((op == ">" && key > value) || (op == "<" && key < value) ||
//                     (op == "=" && key == value) || (op == ">=" && key >= value) ||
//                     (op == "<=" && key <= value) || (op == "!=" && key != value)) {
//                     while (getline(ss, token, ',')) {
//                         rowIndices.push_back(stoi(token));
//                     }
//                 }
//             }
//             inFile.close();
//         }

//         vector<vector<int>> resultRows;
//         Table* table = tableCatalogue.getTable(tableName);
//         if (table) {
//             printVector(table->columns);
//             for (int idx : rowIndices) {
//                 // resultRows.push_back(table->getRow(idx));
//                 printVector(table->getRow(idx));
//             }
//         }

//         // return resultRows;
//     }

//     vector<int> rangeSearchIndex(string op, int value) {
//         vector<int> rowIndices;

//         for (auto& [key, rows] : memtable) {
//             if ((op == ">" && key > value) || (op == "<" && key < value) ||
//                 (op == "=" && key == value) || (op == ">=" && key >= value) ||
//                 (op == "<=" && key <= value) || (op == "!=" && key != value)) {
//                 rowIndices.insert(rowIndices.end(), rows.begin(), rows.end());
//             }
//         }

//         for (auto& file : sstableFiles) {
//             ifstream inFile(file);
//             string line;
//             while (getline(inFile, line)) {
//                 stringstream ss(line);
//                 string token;
//                 getline(ss, token, ',');
//                 int key = stoi(token);
//                 if ((op == ">" && key > value) || (op == "<" && key < value) ||
//                     (op == "=" && key == value) || (op == ">=" && key >= value) ||
//                     (op == "<=" && key <= value) || (op == "!=" && key != value)) {
//                     while (getline(ss, token, ',')) {
//                         rowIndices.push_back(stoi(token));
//                     }
//                 }
//             }
//             inFile.close();
//         }
//         return rowIndices;
//     }

//     void insert(int key, int rowIndex) {
//         memtable[key].push_back(rowIndex);
//         if (memtable.size() >= MEMTABLE_LIMIT) {
//             flushToDisk();
//         }

//         Table* table = tableCatalogue.getTable(tableName);
//         if (table) {
//             // table->insertRow(row);
//         }
//     }

//     void update(string key, int value, int rowIndex) {
//         Table* table = tableCatalogue.getTable(tableName);
//         if (table) {
//             vector<int> row = table->getRow(rowIndex);
//             table->updateRow(rowIndex, key, value);
//         }
//     }

//     void remove(int key, int rowIndex) {
//         auto it = memtable.find(key);
//         if (it != memtable.end()) {
//             auto& vec = it->second;
//             // vec.erase(remove(vec.begin(), vec.end(), rowIndex), vec.end());
//             if (vec.empty()) {
//                 memtable.erase(it);
//             }
//         }

//         Table* table = tableCatalogue.getTable(tableName);
//         if (table) {
//             table->deleteRow(rowIndex);
//         }
//     }
// };