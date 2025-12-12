#include "lsmIndex.h"
/**
 * @brief 
 * SYNTAX: R <- SEARCH FROM relation_name WHERE column_name bin_op value
 */
bool syntacticParseSEARCH()
{
    logger.log("syntacticParseSEARCH");
    if (tokenizedQuery.size() > 9 || tokenizedQuery[2] != "SEARCH" || tokenizedQuery[3] != "FROM" || tokenizedQuery[5] != "WHERE")
    {
        cout << "SYNTAX ERROR" << endl;
        return false;
    }
    parsedQuery.queryType = SEARCH;
    parsedQuery.searchResultRelationName = tokenizedQuery[0];
    parsedQuery.searchColumnName = tokenizedQuery[6];
    parsedQuery.searchRelationName = tokenizedQuery[4];
    // parsedQuery.searchWhereValue = stoi(tokenizedQuery[8]);

    regex numeric("[-]?[0-9]+");
    string WhereValue = tokenizedQuery[8];
    if (regex_match(WhereValue, numeric))
        parsedQuery.searchWhereValue = stoi(WhereValue);
    else
    {
        cout << "SYNTAX ERROR: VALUE ERROR" << endl;
        return false;
    }

    string binaryOperator = tokenizedQuery[7];
    parsedQuery.binop = binaryOperator;
    if (binaryOperator == "<"){
        // parsedQuery.searchBinaryOperator = LESS_THAN;
        }
    else if (binaryOperator == ">"){
        // parsedQuery.searchBinaryOperator = GREATER_THAN;
    }
    else if (binaryOperator == ">=" || binaryOperator == "=>"){
        // parsedQuery.searchBinaryOperator = GEQ;
    }
    else if (binaryOperator == "<=" || binaryOperator == "=<"){
        // parsedQuery.searchBinaryOperator = LEQ;
    }
    else if (binaryOperator == "=="){
        // parsedQuery.searchBinaryOperator = EQUAL;
    }
    else if (binaryOperator == "!="){
        // parsedQuery.searchBinaryOperator = NOT_EQUAL;
    }
    else
    {
        cout << "SYNTAX ERROR: BIN OP ERROR" << endl;
        return false;
    }
    
    cout << "SEARCH: SYNTACTIC PARSE done!" << endl;
    return true;
}

bool semanticParseSEARCH()
{
    logger.log("semanticParseSEARCH");

    if (tableCatalogue.isTable(parsedQuery.searchResultRelationName))
    {
        cout << "SEMANTIC ERROR: Resultant relation already exists" << endl;
        return false;
    }

    if (!tableCatalogue.isTable(parsedQuery.searchRelationName))
    {
        cout << "SEMANTIC ERROR: Relation doesn't exist" << endl;
        return false;
    }

    if (!tableCatalogue.isColumnFromTable(parsedQuery.searchColumnName, parsedQuery.searchRelationName))
    {
        cout << "SEMANTIC ERROR: Column doesn't exist in relation" << endl;
        return false;
    }

    cout<<"SEARCH: SEMANTIC PARSE done!"<<endl;
    return true;
}

// bool evaluateBinOp(int value1, int value2, BinaryOperator binaryOperator)
// {
//     switch (binaryOperator)
//     {
//     case LESS_THAN:
//         return (value1 < value2);
//     case GREATER_THAN:
//         return (value1 > value2);
//     case LEQ:
//         return (value1 <= value2);
//     case GEQ:
//         return (value1 >= value2);
//     case EQUAL:
//         return (value1 == value2);
//     case NOT_EQUAL:
//         return (value1 != value2);
//     default:
//         return false;
//     }
// }

void executeSEARCH()
{
    logger.log("executeSEARCH");

    Table* table = tableCatalogue.getTable(parsedQuery.searchRelationName);
    LSMTreeIndex index(table->tableName, parsedQuery.searchColumnName);

    vector<vector<int>> res = index.rangeSearch(parsedQuery.binop, parsedQuery.searchWhereValue);



    Table* resultantTable = new Table(parsedQuery.searchResultRelationName, table->columns);
    tableCatalogue.insertTable(resultantTable);
    bufferManager.writePage(resultantTable->tableName, 0, res, res.size());
    resultantTable->rowsPerBlockCount.push_back(res.size());
    resultantTable->rowCount = res.size();
    resultantTable->blockCount = 1;
    // Cursor cursor = table.getCursor();
    // vector<int> row = cursor.getNext();
    // int firstColumnIndex = table.getColumnIndex(parsedQuery.searchFirstColumnName);
    // int secondColumnIndex;
    // if (parsedQuery.selectType == COLUMN)
    //     secondColumnIndex = table.getColumnIndex(parsedQuery.searchSecondColumnName);
    // while (!row.empty())
    // {

    //     int value1 = row[firstColumnIndex];
    //     int value2;
    //     if (parsedQuery.selectType == INT_LITERAL)
    //         value2 = parsedQuery.searchIntLiteral;
    //     else
    //         value2 = row[secondColumnIndex];
    //     if (evaluateBinOp(value1, value2, parsedQuery.searchBinaryOperator))
    //         resultantTable->writeRow<int>(row);
    //     row = cursor.getNext();
    // }
    // if(resultantTable->blockify())
    //     tableCatalogue.insertTable(resultantTable);
    // else{
    //     cout<<"Empty Table"<<endl;
    //     resultantTable->unload();
    //     delete resultantTable;
    // }
    return;
}