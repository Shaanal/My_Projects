#include "global.h"
/**
 * @brief 
 * SYNTAX: R <- JOIN relation_name1, relation_name2 ON column_name1 bin_op column_name2
 */
bool syntacticParseJOIN()
{
    logger.log("syntacticParseJOIN");
    if (tokenizedQuery.size() != 8 || tokenizedQuery[5] != "ON")
    {
        cout << "SYNTAC ERROR" << endl;
        return false;
    }
    parsedQuery.queryType = JOIN;
    parsedQuery.joinResultRelationName = tokenizedQuery[0];
    parsedQuery.joinFirstRelationName = tokenizedQuery[3];
    parsedQuery.joinSecondRelationName = tokenizedQuery[4];
    parsedQuery.joinFirstColumnName = tokenizedQuery[6];
    parsedQuery.joinSecondColumnName = tokenizedQuery[7];

    // string binaryOperator = tokenizedQuery[7];
    // if (binaryOperator == "<")
    //     parsedQuery.joinBinaryOperator = LESS_THAN;
    // else if (binaryOperator == ">")
    //     parsedQuery.joinBinaryOperator = GREATER_THAN;
    // else if (binaryOperator == ">=" || binaryOperator == "=>")
    //     parsedQuery.joinBinaryOperator = GEQ;
    // else if (binaryOperator == "<=" || binaryOperator == "=<")
    //     parsedQuery.joinBinaryOperator = LEQ;
    // else if (binaryOperator == "==")
    //     parsedQuery.joinBinaryOperator = EQUAL;
    // else if (binaryOperator == "!=")
    //     parsedQuery.joinBinaryOperator = NOT_EQUAL;
    // else
    // {
    //     cout << "SYNTAX ERROR" << endl;
    //     return false;
    // }
    return true;
}

bool semanticParseJOIN()
{
    logger.log("semanticParseJOIN");

    if (tableCatalogue.isTable(parsedQuery.joinResultRelationName))
    {
        cout << "SEMANTIC ERROR: Resultant relation already exists" << endl;
        return false;
    }

    if (!tableCatalogue.isTable(parsedQuery.joinFirstRelationName) || !tableCatalogue.isTable(parsedQuery.joinSecondRelationName))
    {
        cout << "SEMANTIC ERROR: Relation doesn't exist" << endl;
        return false;
    }

    if (!tableCatalogue.isColumnFromTable(parsedQuery.joinFirstColumnName, parsedQuery.joinFirstRelationName) || !tableCatalogue.isColumnFromTable(parsedQuery.joinSecondColumnName, parsedQuery.joinSecondRelationName))
    {
        cout << "SEMANTIC ERROR: Column doesn't exist in relation" << endl;
        return false;
    }
    return true;
}

void executeJOIN()
{
    logger.log("executeJOIN");
    string table1 = parsedQuery.joinFirstRelationName, table2 = parsedQuery.joinSecondRelationName;
    string col1 = parsedQuery.joinFirstColumnName, col2 = parsedQuery.joinSecondColumnName;
    string restable = parsedQuery.joinResultRelationName;
    int numPartitions = 10;
    Table *table = tableCatalogue.getTable(table1);
    table->hashJoin(table2, col1, col2, restable);
    return;
}