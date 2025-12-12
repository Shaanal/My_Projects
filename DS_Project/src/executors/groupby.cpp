#include "global.h"
/**
 * @brief File contains method to process SORT commands.
 * 
 * syntax:
 * Result-table <- GROUP BY 〈attribute1〉
 *  FROM 〈table〉
 *  HAVING 〈Aggregate-Func1(attribute2)〉 〈bin-op〉 〈attribute-value〉
 *  RETURN 〈Aggregate-Func2(attribute3)〉
 * 
 * sorting_order = ASC | DESC 
 */

                
bool syntacticParseGROUPBY() 
{
    logger.log("syntacticParseGROUPBY");

    if(tokenizedQuery.size()!= 13 || tokenizedQuery[3] != "BY" || tokenizedQuery[5] != "FROM" || tokenizedQuery[7] != "HAVING" || tokenizedQuery[11] != "RETURN"){
        cout<<"SYNTAX ERROR"<<endl;
        return false;
    }

    parsedQuery.queryType = GROUPBY;
    parsedQuery.groupbyResultRelationName = tokenizedQuery[0];
    parsedQuery.groupbyRelationName = tokenizedQuery[6];
    parsedQuery.groupbyColumnName = tokenizedQuery[4];

    string havingExpr = tokenizedQuery[8]; 
    string binOp = tokenizedQuery[9]; 
    string returnExpr = tokenizedQuery[12]; 

    size_t openParenh = havingExpr.find('(');
    size_t closeParenh = havingExpr.find(')');
    if (openParenh == string::npos || closeParenh == string::npos || openParenh > closeParenh) {
        cout << "SYNTAX ERROR: Invalid HAVING condition format" << endl;
        return false;
    }

    size_t openParenr = returnExpr.find('(');
    size_t closeParenr = returnExpr.find(')');
    if (openParenr == string::npos || closeParenr == string::npos || openParenr > closeParenr) {
        cout << "SYNTAX ERROR: Invalid RETURN condition format" << endl;
        return false;
    }

    if (binOp == "<")
        parsedQuery.groupbyBinaryOperator = LESS_THAN;
    else if (binOp == ">")
        parsedQuery.groupbyBinaryOperator = GREATER_THAN;
    else if (binOp == ">=")
        parsedQuery.groupbyBinaryOperator = GEQ;
    else if (binOp == "<=")
        parsedQuery.groupbyBinaryOperator = LEQ;
    else if (binOp == "==")
        parsedQuery.groupbyBinaryOperator = EQUAL;
    else
    {
        cout << "SYNTAX ERROR: BinOP" << endl;
        return false;
    }
    
    parsedQuery.groupbyHavingColumnName = havingExpr.substr(openParenh + 1, closeParenh - openParenh - 1);
    parsedQuery.groupbyHavingValue = tokenizedQuery[10];
    parsedQuery.groupbyReturnColumnName = returnExpr.substr(openParenr + 1, closeParenr - openParenr - 1);

    havingExpr = havingExpr.substr(0, openParenh);
    returnExpr = returnExpr.substr(0, openParenr);
    if (havingExpr == "MAX")
        parsedQuery.groupbyHavingAggrFunc = MAX;
    else if (havingExpr == "MIN")
        parsedQuery.groupbyHavingAggrFunc = MIN;
    else if (havingExpr == "SUM")
        parsedQuery.groupbyHavingAggrFunc = SUM;
    else if (havingExpr == "AVG")
        parsedQuery.groupbyHavingAggrFunc = AVG;
    else if (havingExpr == "COUNT")
        parsedQuery.groupbyHavingAggrFunc = COUNT;
    else
    {
        cout << "SYNTAX ERROR: HavingAggrFunc" << endl;
        return false;
    }
    if (returnExpr == "MAX")
        parsedQuery.groupbyReturnAggrFunc = MAX;
    else if (returnExpr == "MIN")
        parsedQuery.groupbyReturnAggrFunc = MIN;
    else if (returnExpr == "SUM")
        parsedQuery.groupbyReturnAggrFunc = SUM;
    else if (returnExpr == "AVG")
        parsedQuery.groupbyReturnAggrFunc = AVG;
    else if (returnExpr == "COUNT")
        parsedQuery.groupbyReturnAggrFunc = COUNT;
    else
    {
        cout << "SYNTAX ERROR: ReturnAggrFunc" << endl;
        return false;
    }
   
    cout<<"GROUPBY:SYNTACTIC PARSE done!"<<endl;
    return true;
}


bool semanticParseGROUPBY()
{
    logger.log("semanticParseGROUPBY");

    if(tableCatalogue.isTable(parsedQuery.groupbyResultRelationName)){
        cout<<"SEMANTIC ERROR: Resultant relation already exists"<<endl;
        return false;
    }

    if (!tableCatalogue.isTable(parsedQuery.groupbyRelationName)) {
        cout << "SEMANTIC ERROR: Table " << parsedQuery.groupbyRelationName << " does not exist" << endl;
        return false;
    }

    Table *table = tableCatalogue.getTable(parsedQuery.groupbyRelationName);
    
    if(!table->isColumn(parsedQuery.groupbyColumnName)){
        cout<<"SEMANTIC ERROR: Column doesn't exist in relation"<<endl;
        return false;
    }
    if(!table->isColumn(parsedQuery.groupbyHavingColumnName)){
        cout<<"SEMANTIC ERROR: Column doesn't exist in relation"<<endl;
        return false;
    }
    if(!table->isColumn(parsedQuery.groupbyReturnColumnName)){
        cout<<"SEMANTIC ERROR: Column doesn't exist in relation"<<endl;
        return false;
    }
    
    if (parsedQuery.groupbyHavingAggrFunc == COUNT && parsedQuery.groupbyReturnAggrFunc == COUNT) {
        cout << "SEMANTIC ERROR: COUNT function cannot be used in both HAVING and RETURN clauses" << endl;
        return false;
    }
    cout<<"GROUPBY:SEMANTIC PARSE done!"<<endl;
    return true;
}

void executeGROUPBY() 
{
    logger.log("executeGROUPBY");
    Table* table = tableCatalogue.getTable(parsedQuery.groupbyRelationName);
    if (!table) {
        cout << "ERROR: Table not found" << endl;
        return;
    }

    string resultTableName = parsedQuery.groupbyResultRelationName;
    if (tableCatalogue.isTable(resultTableName)) {
        cout << "ERROR: Resultant table already exists" << endl;
        return;
    }

    parsedQuery.sortRelationName = parsedQuery.groupbyRelationName;
    parsedQuery.sortColumnNames = {parsedQuery.groupbyColumnName};
    parsedQuery.sortingStrategies = {ASC};
    executeKWAYSORT();

    int groupByColumnIndex = table->getColumnIndex(parsedQuery.groupbyColumnName);
    int havingColumnIndex = table->getColumnIndex(parsedQuery.groupbyHavingColumnName);
    int returnColumnIndex = table->getColumnIndex(parsedQuery.groupbyReturnColumnName);

    if (groupByColumnIndex == -1 || havingColumnIndex == -1 || returnColumnIndex == -1) {
        cout << "ERROR: Column not found in table" << endl;
        return;
    }

    int bufferSize = 10;
    vector<vector<vector<int>>> buffer(bufferSize);
    // unordered_map<int, vector<int>> groupAggregates;
    map<int, vector<int>> groupAggregates;
    
    int pageIndex = 0;
    bool doneReading = false;

    while (!doneReading) {
        for (int i = 0; i < bufferSize - 1; i++) {
            buffer[i] = bufferManager.readPage(parsedQuery.sortRelationName, pageIndex++);
            if (buffer[i].empty()) {
                doneReading = true;
                break;
            }
        }

        for (int i = 0; i < bufferSize - 1; i++) {
            for (auto& row : buffer[i]) {
                int groupValue = row[groupByColumnIndex];
                int havingValue = row[havingColumnIndex];
                int returnValue = row[returnColumnIndex];

                if (groupAggregates.find(groupValue) == groupAggregates.end()) {
                    groupAggregates[groupValue] = {0, 0, 0, INT_MIN, INT_MAX, INT_MIN, INT_MAX};
                }

                groupAggregates[groupValue][0]++;
                groupAggregates[groupValue][1] += havingValue;
                groupAggregates[groupValue][2] += returnValue;
                groupAggregates[groupValue][3] = max(groupAggregates[groupValue][3], havingValue);
                groupAggregates[groupValue][4] = min(groupAggregates[groupValue][4], havingValue);
                groupAggregates[groupValue][5] = max(groupAggregates[groupValue][5], returnValue);
                groupAggregates[groupValue][6] = min(groupAggregates[groupValue][6], returnValue);
            }
        }
    }

    string aggstring = "";
    switch (parsedQuery.groupbyReturnAggrFunc) {
            case COUNT: aggstring = "COUNT"; break;
            case SUM: aggstring = "SUM"; break;
            case AVG: aggstring = "AVG"; break;
            case MAX: aggstring = "MAX"; break;
            case MIN: aggstring = "MIN"; break;
            default: break;
        }
    string returnColumnName = aggstring + parsedQuery.groupbyReturnColumnName;
    vector<string> resultColumns = {parsedQuery.groupbyColumnName, returnColumnName};
    
    Table* resultTable = new Table(resultTableName, resultColumns);
    resultTable->columnCount = 2;

    int resultPageIndex = 0;
    buffer[bufferSize - 1].clear();
    int totalRowCount = 0;

    for (auto& [groupValue, aggregates] : groupAggregates) {
        double havingAggregate = 0;
        double returnAggregate = 0;

        switch (parsedQuery.groupbyHavingAggrFunc) {
            case COUNT: havingAggregate = aggregates[0]; break;
            case SUM: havingAggregate = aggregates[1]; break;
            case AVG: havingAggregate = (double)aggregates[1] / aggregates[0]; break;
            case MAX: havingAggregate = aggregates[3]; break;
            case MIN: havingAggregate = aggregates[4]; break;
            default: break;
        }

        switch (parsedQuery.groupbyReturnAggrFunc) {
            case COUNT: returnAggregate = aggregates[0]; break;
            case SUM: returnAggregate = aggregates[2]; break;
            case AVG: returnAggregate = (double)aggregates[2] / aggregates[0]; break;
            case MAX: returnAggregate = aggregates[5]; break;
            case MIN: returnAggregate = aggregates[6]; break;
            default: break;
        }

        bool conditionMet = false;
        switch (parsedQuery.groupbyBinaryOperator) {
            case LESS_THAN: conditionMet = havingAggregate < stoi(parsedQuery.groupbyHavingValue); break;
            case GREATER_THAN: conditionMet = havingAggregate > stoi(parsedQuery.groupbyHavingValue); break;
            case LEQ: conditionMet = havingAggregate <= stoi(parsedQuery.groupbyHavingValue); break;
            case GEQ: conditionMet = havingAggregate >= stoi(parsedQuery.groupbyHavingValue); break;
            case EQUAL: conditionMet = havingAggregate == stoi(parsedQuery.groupbyHavingValue); break;
            default: break;
        }

        if (conditionMet) {
            vector<int> newRow = {groupValue, (int)returnAggregate};
            resultTable->writeRow(newRow);
            totalRowCount++;
        }
    }

    resultTable->blockify();
    resultTable->rowCount = totalRowCount;
    tableCatalogue.insertTable(resultTable);

    cout << "Result stored in table: " << resultTableName << endl;
    cout << "GROUPBY: EXECUTION done!" << endl;
}
