#include "global.h"
/**
 * @brief File contains method to process SORT commands.
 * 
 * syntax:
 * R <- ORDER BY column_name sorting_order ON relation_name
 * 
 * sorting_order = ASC | DESC 
 */

void sort_subfile_o(int k, vector<vector<vector<int>>> &buffer, Table* resultTable, int pageIndex)
{
    auto compare = [&](pair<int, vector<int>> a, pair<int, vector<int>> b) {
        // for (int i = 0; i < parsedQuery.sortColumnNames.size(); i++) {
            int colIndex = resultTable->getColumnIndex(parsedQuery.sortColumnName);
            if (a.second[colIndex] != b.second[colIndex]) {
                return parsedQuery.sortingStrategy == ASC ? a.second > b.second : a.second < b.second;
            }
        // }
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
    
    int rowsPerPage = resultTable->maxRowsPerBlock;
    int rowCount = 1;

    while (!pq.empty()) {
        auto [blockIndex, row] = pq.top();
        pq.pop();

        if(rowCount<=rowsPerPage)   
            bufferManager.writePageRow(resultTable->tableName, pageIndex, row, rowCount++);
        else{
            pageIndex++;
            rowCount = 1;
            bufferManager.writePageRow(resultTable->tableName, pageIndex, row, rowCount++);
        }  

        if (blockIndices_k[blockIndex] < buffer[blockIndex].size()) {
            pq.push({blockIndex, buffer[blockIndex][blockIndices_k[blockIndex]]});
            blockIndices_k[blockIndex]++;
        }
    }

}



bool syntacticParseORDERBY() {
    logger.log("syntacticParseORDERBY");

    if(tokenizedQuery.size()!= 8 || tokenizedQuery[3] != "BY" || tokenizedQuery[6] != "ON"){
        cout<<"SYNTAX ERROR"<<endl;
        return false;
    }

    parsedQuery.queryType = ORDERBY;
    parsedQuery.sortResultRelationName = tokenizedQuery[0];
    parsedQuery.sortRelationName = tokenizedQuery[7];
    parsedQuery.sortColumnName = tokenizedQuery[4];
    string sortingStrategy = tokenizedQuery[5];
    if(sortingStrategy == "ASC")
        parsedQuery.sortingStrategy = ASC;
    else if(sortingStrategy == "DESC")
        parsedQuery.sortingStrategy = DESC;
    else{
        cout<<"SYNTAX ERROR"<<endl;
        return false;
    }
    
    cout<<"ORDERBY: SYNTACTIC PARSE done!"<<endl;
    return true;
}


bool semanticParseORDERBY(){
    logger.log("semanticParseORDERBY");

    if(tableCatalogue.isTable(parsedQuery.sortResultRelationName)){
        cout<<"SEMANTIC ERROR: Resultant relation already exists"<<endl;
        return false;
    }

    if(!tableCatalogue.isTable(parsedQuery.sortRelationName)){
        cout<<"SEMANTIC ERROR: Relation doesn't exist"<<endl;
        return false;
    }

    if(!tableCatalogue.isColumnFromTable(parsedQuery.sortColumnName, parsedQuery.sortRelationName)){
        cout<<"SEMANTIC ERROR: Column doesn't exist in relation"<<endl;
        return false;
    }

    cout<<"ORDERBY: SEMANTIC PARSE done!"<<endl;
    return true;
}

void executeORDERBY() {
    logger.log("executeORDERBY");

    Table* table = tableCatalogue.getTable(parsedQuery.sortRelationName);
    if (!table) {
        cout << "ERROR: Table not found" << endl;
        return;
    }
    
    Table* resultTable = new Table(parsedQuery.sortResultRelationName, table->columns);
    resultTable->maxRowsPerBlock = table->maxRowsPerBlock;
    
    tableCatalogue.insertTable(resultTable);

    int totalBlocks = table->blockCount; //-------b
    int bufferSize = 10;
    int k = bufferSize;                              //-------k
    int numSubfiles = ceil((double)totalBlocks / k); //-------m
    vector<vector<vector<int>>> buffer;

    int page_Index = 0;
    int pI = 0;
    int qI = 0;

    auto compare = [&](pair<int, vector<int>> a, pair<int, vector<int>> b) {
        int colIndex = resultTable->getColumnIndex(parsedQuery.sortColumnName);
        if (a.second[colIndex] != b.second[colIndex]) {
            return parsedQuery.sortingStrategy == ASC ? a.second[colIndex] > b.second[colIndex] : a.second[colIndex] < b.second[colIndex];
        }
        return false;
    };

    vector<pair<int, int>> subfilePageIndices;
    int totalRowCount = 0;

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
                int colIndex = table->getColumnIndex(parsedQuery.sortColumnName);
                if (a[colIndex] != b[colIndex]) {
                    return parsedQuery.sortingStrategy == ASC ? a[colIndex] < b[colIndex] : a[colIndex] > b[colIndex];
                }
                return false;
            });

            for (vector<int> row : buffer[blockIndex])
            {
                resultTable->writeRow(row);
                totalRowCount++;
            }
            pI++;
        }

        page_Index = pI;  
        buffer.clear();
    }
    resultTable->blockify();
    resultTable->rowCount = totalRowCount;
    tableCatalogue.updateTable(resultTable);
    
    page_Index = 0;
    pI = 0;

    for (int i = 0; i < numSubfiles; i++)
    {
        buffer = vector<vector<vector<int>>>(bufferSize);
        int startPageIndex = page_Index; 
        int startBlock = i * (k-1);
        int endBlock = min((i + 1) * (k-1), totalBlocks);

        for (int j = startBlock; j < endBlock; j++)
        {
            int blockIndex = j-startBlock;
            buffer[blockIndex] = bufferManager.readPage(resultTable->tableName, j);

            if (buffer[blockIndex].empty())
            {
                cout << "ERROR: Failed to read block " << j << " from table " << resultTable->tableName << endl;
                return;
            }
            pI++;
        }

        sort_subfile_o(k, buffer, resultTable, page_Index);
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
       
    while (currentPass <= mergePasses) {
        int nextPassFiles = ceil((double)remainingFiles / (bufferSize - 1));
        int subfileIndex = 1;

        for (int i = 0; i < currentPassFiles; i++) {
            int startPage = subfilePageIndices[i].first;
            buffer[i] = bufferManager.readPage(resultTable->tableName, startPage);
            if (!buffer[i].empty()) {
                pq.push({i, buffer[i][0]});
                buffer[i].erase(buffer[i].begin());
                blockIndices_m[i]++;
            }
        }

        while(subfileIndex <= nextPassFiles) {

            while (!pq.empty()) {
                auto [blockIndex, row] = pq.top();
                pq.pop();

                buffer[k-1].push_back(row);
                if (buffer[k-1].size() == resultTable->maxRowsPerBlock) {
                    bufferManager.writePage(resultTable->tableName, pageIndex++, buffer[k-1], buffer[k-1].size());
                    resultTable->rowsPerBlockCount.emplace_back(buffer[k-1].size());
                    buffer[k-1].clear();
                }

                if (!buffer[blockIndex].empty()) {
                    pq.push({blockIndex, buffer[blockIndex][0]});
                    buffer[blockIndex].erase(buffer[blockIndex].begin());
                }
                else if (blockIndices_m[blockIndex] < 10) {
                    int nextPage = subfilePageIndices[blockIndex].first + blockIndices_m[blockIndex];
                    if (nextPage <= subfilePageIndices[blockIndex].second) {
                        buffer[blockIndex] = bufferManager.readPage(resultTable->tableName, nextPage);
                        if (!buffer[blockIndex].empty()) {
                            pq.push({blockIndex, buffer[blockIndex][0]});
                            buffer[blockIndex].erase(buffer[blockIndex].begin());
                            blockIndices_m[blockIndex]++;
                        }
                    }
                }
            }
            subfileIndex++;
        }
        remainingFiles = nextPassFiles;
        currentPass++;
    }
    if (!buffer[k-1].empty()) {
        bufferManager.writePage(resultTable->tableName, pageIndex++, buffer[k-1], buffer[k-1].size());
        resultTable->rowsPerBlockCount.emplace_back(buffer[k-1].size());
    }

    int bc = resultTable->blockCount;

    Cursor c= resultTable->getCursor();
    c.nextPage(bc);
    buffer = vector<vector<vector<int>>>(1);
    buffer[0] = c.getNextpage();
    bufferManager.writePage(parsedQuery.sortResultRelationName, bc-bc, buffer[0], buffer[0].size());
    
    bufferManager.deleteFile(resultTable->tableName, "t");
    resultTable->writeRow<string>(resultTable->columns);

    for(int q = bc; q < pageIndex; q++)
    {
        c.nextPage(q);

        buffer[0] = c.getNextpage();
        bufferManager.writePage(parsedQuery.sortResultRelationName, q-bc, buffer[0], buffer[0].size());
        
        for(int r = 0; r < resultTable->maxRowsPerBlock; r++)
        {
            resultTable->writeRow(buffer[0][r]);
        }
    }
    buffer[0].clear();

    for(int j = bc; j < pageIndex; j++)
    {
        bufferManager.deleteFile(parsedQuery.sortResultRelationName, j);
    }    
    
    cout << "Result stored in table: " << resultTable->tableName << endl;
    cout << "ORDERBY: EXECUTION done!" << endl;

    return;
}
