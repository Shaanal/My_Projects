#include "lsmIndex.h"
//  syntax UPDATE table_name WHERE condition SET col_name = value
/**
 * @brief File contains method to process UPDATE commands.
 *
 * syntax:
 * UPDATE table_name WHERE col_name operator value SET col_name2 = value
 */

bool syntacticParseUPDATE()
{
    logger.log("syntacticParseUPDATE");

    if (tokenizedQuery.size() != 10 || tokenizedQuery[2] != "WHERE" || tokenizedQuery[6] != "SET" || tokenizedQuery[8] != "=")
    {
        cout << "SYNTAX ERROR 1" << endl;
        return false;
    }

    parsedQuery.queryType = UPDATE;
    parsedQuery.updateTableName = tokenizedQuery[1];
    parsedQuery.updateColumnName_where = tokenizedQuery[3];
    parsedQuery.updateSetColumnName = tokenizedQuery[7];

    regex numeric("[-]?[0-9]+");
    string WhereValue = tokenizedQuery[5];
    if (regex_match(WhereValue, numeric))
        parsedQuery.updateValue_where = stoi(WhereValue);
    else
    {
        cout << "SYNTAX ERROR: VALUE ERROR" << endl;
        return false;
    }
    string binaryOperator = tokenizedQuery[4];
    parsedQuery.binop = binaryOperator;
    if (binaryOperator == "<")
        parsedQuery.updateOperatorType_where = LESS_THAN;
    else if (binaryOperator == ">")
        parsedQuery.updateOperatorType_where = GREATER_THAN;
    else if (binaryOperator == ">=" || binaryOperator == "=>")
        parsedQuery.updateOperatorType_where = GEQ;
    else if (binaryOperator == "<=" || binaryOperator == "=<")
        parsedQuery.updateOperatorType_where = LEQ;
    else if (binaryOperator == "==")
        parsedQuery.updateOperatorType_where = EQUAL;
    else if (binaryOperator == "!=")
        parsedQuery.updateOperatorType_where = NOT_EQUAL;
    else
    {
        cout << "SYNTAX ERROR: BIN OP ERROR" << endl;
        return false;
    }
    string setValue = tokenizedQuery[9];
    // parsedQuery.setValue = setValue;
    if (regex_match(setValue, numeric))
        parsedQuery.updateSetValue = stoi(setValue);
    else
    {
        cout << "SYNTAX ERROR: VALUE ERROR" << endl;
        return false;
    }
    cout << "UPDATE: SYNTACTIC PARSE done!" << endl;

    return true;
}

bool semanticParseUPDATE()
{
    logger.log("semanticParseUPDATE");

    if (!tableCatalogue.isTable(parsedQuery.updateTableName))
    {
        cout << "SEMANTIC ERROR: Relation doesn't exist" << endl;
        return false;
    }

    if (!tableCatalogue.isColumnFromTable(parsedQuery.updateColumnName_where, parsedQuery.updateTableName))
    {
        cout << "SEMANTIC ERROR: Column doesn't exist in relation" << endl;
        return false;
    }

    if (!tableCatalogue.isColumnFromTable(parsedQuery.updateSetColumnName, parsedQuery.updateTableName))
    {
        cout << "SEMANTIC ERROR: Column doesn't exist in relation" << endl;
        return false;
    }

    cout << "UPDATE: SEMANTIC PARSE done!" << endl;

    return true;
}

void executeUPDATE()
{
    logger.log("executeUPDATE");

    Table* table = tableCatalogue.getTable(parsedQuery.updateTableName);
    LSMTreeIndex index(table->tableName, parsedQuery.updateColumnName_where);
    vector<int> res_idx = index.rangeSearchIndex(parsedQuery.binop, parsedQuery.updateValue_where);
    index.update(res_idx, parsedQuery.updateSetColumnName, parsedQuery.updateSetValue);

    cout << "UPDATE: EXECUTE done!" << endl;
}
