#include "global.h"
/**
 * @brief File contains method to process SORT commands.
 *
 * syntax:
 * SORT relation_name BY col1,col2 col3 IN sorting_order1, sorting_order2, sorting_order3
 *
 * sorting_order = ASC | DESC
 *
 * eg.: LOAD A
 *      SORT A BY b,c IN ASC, DESC
 */

void sort_subfile(int k, vector<vector<vector<int>>> &buffer, Table* table, int pageIndex)
{
    auto compare = [&](pair<int, vector<int>> a, pair<int, vector<int>> b) {
        for (int i = 0; i < parsedQuery.sortColumnNames.size(); i++) {
            int colIndex = table->getColumnIndex(parsedQuery.sortColumnNames[i]);
            if (a.second[colIndex] != b.second[colIndex]) {
                return parsedQuery.sortingStrategies[i] == ASC ? a.second[colIndex] > b.second[colIndex] : a.second[colIndex] < b.second[colIndex];
            }
        }
        return false;
        };

    priority_queue<pair<int, vector<int>>, vector<pair<int, vector<int>>>, decltype(compare)> pq(compare);
    vector<int> blockIndices_k(k, 0);

    for (int i = 0; i < k; i++) {
        if (!buffer[i].empty() && blockIndices_k[i] < buffer[i].size()) {
            pq.push({i, buffer[i][blockIndices_k[i]]});
            blockIndices_k[i]++;
        }
    }
    
    // vector<vector<int>> mergedPage;
    int rowsPerPage = table->maxRowsPerBlock;
    int rowCount = 1;

    while (!pq.empty()) {
        auto [blockIndex, row] = pq.top();
        pq.pop();

        // buffer[k-1].push_back(row);
        if(rowCount<=rowsPerPage)   
            bufferManager.writePageRow(table->tableName, pageIndex, row, rowCount++);
        else{
            pageIndex++;
            rowCount = 1;
            bufferManager.writePageRow(table->tableName, pageIndex, row, rowCount++);
        }  

        // if (buffer[k-1].size() == rowsPerPage) {
        //     bufferManager.writePage(table->tableName, pageIndex++, buffer[k-1], buffer[k-1].size());
        //     buffer[k-1].clear();
        // }

        if (blockIndices_k[blockIndex] < buffer[blockIndex].size()) {
            pq.push({blockIndex, buffer[blockIndex][blockIndices_k[blockIndex]]});
            blockIndices_k[blockIndex]++;
        }
    }

    // if (!buffer[k-1].empty()) {
    //     bufferManager.writePage(table->tableName, pageIndex++, buffer[k-1], buffer[k-1].size());
    // }

}

bool syntacticParseKWAYSORT()
{
    logger.log("syntacticParseKWAYSORT");

    if (tokenizedQuery[2] != "BY")
    {
        cout << "SYNTAX ERROR: Missing 'BY'" << endl;
        return false;
    }

    auto inPos = find(tokenizedQuery.begin(), tokenizedQuery.end(), "IN");
    if (inPos == tokenizedQuery.end())
    {
        cout << "SYNTAX ERROR: Missing 'IN'" << endl;
        return false;
    }

    parsedQuery.queryType = KWAYSORT;
    parsedQuery.sortRelationName = tokenizedQuery[1];
    parsedQuery.sortColumnNames.clear();
    for (auto it = tokenizedQuery.begin() + 3; it != inPos; ++it)
    {
        if (*it != ",")
        {
            parsedQuery.sortColumnNames.push_back(*it);
        }
    }
    parsedQuery.sortingStrategies.clear();
    for (auto it = inPos + 1; it != tokenizedQuery.end(); ++it)
    {
        if (*it == ",")
            continue;
        if (*it == "ASC")
            parsedQuery.sortingStrategies.push_back(ASC);
        else if (*it == "DESC")
            parsedQuery.sortingStrategies.push_back(DESC);
        else
        {
            cout << "SYNTAX ERROR: Invalid sorting order '" << *it << "'" << endl;
            return false;
        }
    }
    if (parsedQuery.sortColumnNames.size() != parsedQuery.sortingStrategies.size())
    {
        cout << "SYNTAX ERROR: Number of columns and sorting orders do not match" << endl;
        return false;
    }
    cout << "KWAYSORT: SYNTACTIC PARSE done!" << endl;
    return true;
}


bool semanticParseKWAYSORT()
{
    logger.log("semanticParseKWAYSORT");

    if (!tableCatalogue.isTable(parsedQuery.sortRelationName))
    {
        cout << "SEMANTIC ERROR: Table " << parsedQuery.sortRelationName << " does not exist" << endl;
        return false;
    }

    Table *table = tableCatalogue.getTable(parsedQuery.sortRelationName);

    for (string column : parsedQuery.sortColumnNames)
    {
        if (!table->isColumn(column))
        {
            cout << "SEMANTIC ERROR: Column " << column << " does not exist in table " << parsedQuery.sortRelationName << endl;
            return false;
        }
    }
    cout << "KWAYSORT: SEMANTIC PARSE done!" << endl;
    return true;
}


void executeKWAYSORT()
{
    logger.log("executeKWAYSORT");

    Table *table = tableCatalogue.getTable(parsedQuery.sortRelationName);
    if (!table)
    {
        cout << "ERROR: Table not found" << endl;
        return;
    }

    int totalBlocks = table->blockCount; //-------b
    int bufferSize = 10;
    int k = bufferSize;                              //-------k
    int numSubfiles = ceil((double)totalBlocks / k); //-------m
    vector<vector<vector<int>>> buffer;

    int page_Index = 0;
    int pI = 0;
    int qI = 0;

    auto compare = [&](pair<int, vector<int>> a, pair<int, vector<int>> b) {
        for (int i = 0; i < parsedQuery.sortColumnNames.size(); i++) {
            int colIndex = table->getColumnIndex(parsedQuery.sortColumnNames[i]);
            if (a.second[colIndex] != b.second[colIndex]) {
                return parsedQuery.sortingStrategies[i] == ASC ? a.second[colIndex] > b.second[colIndex] : a.second[colIndex] < b.second[colIndex];
            }
        }
        return false;
        };

    vector<pair<int, int>> subfilePageIndices;

    for (int i = 0; i < numSubfiles; i++)
    {
        buffer = vector<vector<vector<int>>>(bufferSize);
        int startPageIndex = page_Index; 
        int startBlock = i * k;
        int endBlock = min((i + 1) * k, totalBlocks);

        for (int j = startBlock; j < endBlock; j++)
        {
            int blockIndex = j-startBlock;
            buffer[blockIndex] = bufferManager.readPage(table->tableName, j);

            if (buffer[blockIndex].empty())
            {
                cout << "ERROR: Failed to read block " << j << " from table " << table->tableName << endl;
                return;
            }

            sort(buffer[blockIndex].begin(), buffer[blockIndex].end(), [&](vector<int> a, vector<int> b)
            {
                for (int i = 0; i < parsedQuery.sortColumnNames.size(); i++) {
                    int colIndex = table->getColumnIndex(parsedQuery.sortColumnNames[i]);
                    if (a[colIndex] != b[colIndex]) {
                        return parsedQuery.sortingStrategies[i] == ASC ? a[colIndex] < b[colIndex] : a[colIndex] > b[colIndex];
                    }
                }
                return false; 
            });

            pI++;
        }

        sort_subfile(k, buffer, table, page_Index);
        page_Index = pI;  
        buffer.clear();
        int endPageIndex = page_Index - 1;  
        subfilePageIndices.push_back({startPageIndex, endPageIndex});
    }

    int pageIndex = subfilePageIndices.back().second + 1; 
    vector<int> blockIndices_m(numSubfiles, 0);
    buffer = vector<vector<vector<int>>>(bufferSize);

    priority_queue<pair<int, vector<int>>, vector<pair<int, vector<int>>>, decltype(compare)> pq(compare);

    int mergePasses = ceil(log(numSubfiles) / log(bufferSize - 1));
    int remainingFiles = numSubfiles;
    int currentPass = 1;

    if (numSubfiles == 1) {
        buffer[0] = bufferManager.readPage(table->tableName, subfilePageIndices[0].first);
        bufferManager.writePage(parsedQuery.sortRelationName, 0, buffer[0], buffer[0].size());
        cout << "KWAYSORT: EXECUTE done!" << endl;
        return;
    }

    int currentPassFiles = 0;
    if (numSubfiles > k-1) {
        currentPassFiles = k-1;
    }
    else {
        currentPassFiles = numSubfiles;
    }
    int idx = 0;
       
    // while (currentPass <= mergePasses) {
    //     int nextPassFiles = ceil((double)remainingFiles / (bufferSize - 1));
        int subfileIndex = 1;

    //     while(subfileIndex <= nextPassFiles) {

            for (int i = 0; i < currentPassFiles; i++) {
                idx = currentPassFiles*(subfileIndex-1) + i;
                int startPage = subfilePageIndices[idx].first;
                buffer[i] = bufferManager.readPage(table->tableName, startPage);
                if (!buffer[i].empty()) {
                    pq.push({i, buffer[i][0]});
                    buffer[i].erase(buffer[i].begin());
                    blockIndices_m[idx]++;
                }
            }

            while (!pq.empty()) {
                auto [blockIndex, row] = pq.top();
                pq.pop();

                buffer[k-1].push_back(row);
                if (buffer[k-1].size() == table->maxRowsPerBlock) {
                    bufferManager.writePage(table->tableName, pageIndex++, buffer[k-1], buffer[k-1].size());
                    table->rowsPerBlockCount.emplace_back(buffer[k-1].size());
                    buffer[k-1].clear();
                }

                if (!buffer[blockIndex].empty()) {
                    pq.push({blockIndex, buffer[blockIndex][0]});
                    buffer[blockIndex].erase(buffer[blockIndex].begin());
                }
                else if (blockIndices_m[blockIndex] < 10) {
                    int nextPage = subfilePageIndices[blockIndex].first + blockIndices_m[blockIndex];
                    if (nextPage <= subfilePageIndices[blockIndex].second) {
                        buffer[blockIndex] = bufferManager.readPage(table->tableName, nextPage);
                        if (!buffer[blockIndex].empty()) {
                            pq.push({blockIndex, buffer[blockIndex][0]});
                            buffer[blockIndex].erase(buffer[blockIndex].begin());
                            blockIndices_m[blockIndex]++;
                        }
                    }
                }
            }
    //         subfileIndex++;
    //     }
    //     remainingFiles = nextPassFiles;
    //     currentPass++;
    // }
    if (!buffer[k-1].empty()) {
        bufferManager.writePage(table->tableName, pageIndex++, buffer[k-1], buffer[k-1].size());
        table->rowsPerBlockCount.emplace_back(buffer[k-1].size());
    }

    int bc = table->blockCount;

    Cursor c= table->getCursor();
    c.nextPage(bc);
    buffer = vector<vector<vector<int>>>(1);
    buffer[0] = c.getNextpage();
    bufferManager.writePage(parsedQuery.sortRelationName, bc-bc, buffer[0], buffer[0].size());

    for(int q = bc; q < pageIndex; q++)
    {
        c.nextPage(q);

        buffer[0] = c.getNextpage();
        bufferManager.writePage(parsedQuery.sortRelationName, q-bc, buffer[0], buffer[0].size());
    }
    buffer[0].clear();

    for(int j = bc; j < pageIndex; j++)
    {
        bufferManager.deleteFile(parsedQuery.sortRelationName, j);
    }
    
    cout << "KWAYSORT: EXECUTE done!" << endl;
    return;   
}
