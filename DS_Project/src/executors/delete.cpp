#include "lsmIndex.h"
//  DELETE FROM table_name WHERE col_name operator value

bool syntacticParseDELETE()
{
    logger.log("syntacticParseDELETE");
    cout << "Address of tableCatalogue inside DELETE: " << &tableCatalogue << endl;

    if (tokenizedQuery.size() != 7 || tokenizedQuery[1] != "FROM" || tokenizedQuery[3] != "WHERE")
    {
        cout << "SYNTAX ERROR 1" << endl;
        return false;
    }

    parsedQuery.queryType = DELETE;
    parsedQuery.deleteTableName = tokenizedQuery[2];
    parsedQuery.deleteColumnName_where = tokenizedQuery[4];

    regex numeric("[-]?[0-9]+");
    string WhereValue = tokenizedQuery[6];
    if (regex_match(WhereValue, numeric))
        parsedQuery.deleteValue_where = stoi(WhereValue);
    else
    {
        cout << "SYNTAX ERROR: VALUE ERROR" << endl;
        return false;
    }
    string binaryOperator = tokenizedQuery[5];
    parsedQuery.binop = binaryOperator;
    if (binaryOperator == "<")
        parsedQuery.deleteOperatorType_where = LESS_THAN;
    else if (binaryOperator == ">")
        parsedQuery.deleteOperatorType_where = GREATER_THAN;
    else if (binaryOperator == ">=" || binaryOperator == "=>")
        parsedQuery.deleteOperatorType_where = GEQ;
    else if (binaryOperator == "<=" || binaryOperator == "=<")
        parsedQuery.deleteOperatorType_where = LEQ;
    else if (binaryOperator == "==")
        parsedQuery.deleteOperatorType_where = EQUAL;
    else if (binaryOperator == "!=")
        parsedQuery.deleteOperatorType_where = NOT_EQUAL;
    else
    {
        cout << "SYNTAX ERROR: BIN OP ERROR" << endl;
        return false;
    }
    
    cout << "DELETE: SYNTACTIC PARSE done!" << endl;

    return true;
}

bool semanticParseDELETE()
{
    logger.log("semanticParseDELETE");


    if (!tableCatalogue.isTable(parsedQuery.deleteTableName))
    {
        cout << "SEMANTIC ERROR: Relation doesn't exist" << endl;
        return false;
    }

    if (!tableCatalogue.isColumnFromTable(parsedQuery.deleteColumnName_where, parsedQuery.deleteTableName))
    {
        cout << "SEMANTIC ERROR: Column doesn't exist in relation" << endl;
        return false;
    }

    cout<<"DELETE: SEMANTIC PARSE done!"<<endl;
    return true;
}

void executeDELETE()
{
    logger.log("executeDELETE");
    Table* table = tableCatalogue.getTable(parsedQuery.deleteTableName);
    LSMTreeIndex index(table->tableName, parsedQuery.deleteColumnName_where);
    vector<int> res_idx = index.rangeSearchIndex(parsedQuery.binop, parsedQuery.deleteValue_where);
    index.remove(res_idx);
    cout << "DELETE: EXECUTE done!" << endl;
}   