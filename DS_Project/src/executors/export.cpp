#include "global.h"

/**
 * @brief 
 * SYNTAX: EXPORT <relation_name> 
 */

// bool syntacticParseEXPORT()
// {
//     logger.log("syntacticParseEXPORT");
//     if (tokenizedQuery.size() != 2)
//     {
//         cout << "SYNTAX ERROR" << endl;
//         return false;
//     }
//     parsedQuery.queryType = EXPORT;
//     parsedQuery.exportRelationName = tokenizedQuery[1];
//     return true;
// }

bool syntacticParseEXPORT()
{
    logger.log("syntacticParseEXPORT");
    if (tokenizedQuery.size() < 2 || tokenizedQuery.size() > 3)
    {
        cout << "SYNTAX ERROR" << endl;
        return false;
    }
    if (tokenizedQuery.size() == 3 && tokenizedQuery[1] == "MATRIX")
    {
        parsedQuery.queryType = EXPORT_MATRIX;
        parsedQuery.loadRelationName = tokenizedQuery[2];
        cout << "SYNTACTIC PARSE of EXPORT DONE" << endl;
    }
    else if (tokenizedQuery.size() == 2)
    {
        parsedQuery.queryType = EXPORT;
        parsedQuery.exportRelationName = tokenizedQuery[1];
    }
    else
    {
        cout << "SYNTAX ERROR" << endl;
        return false;
    }
    return true;
}

// bool semanticParseEXPORT()
// {
//     logger.log("semanticParseEXPORT");
//     //Table should exist
//     if (tableCatalogue.isTable(parsedQuery.exportRelationName))
//         return true;
//     cout << "SEMANTIC ERROR: No such relation exists" << endl;
//     return false;
// }
bool semanticParseEXPORT()
{
    logger.log("semanticParseEXPORT");
    //Table should exist
    if (parsedQuery.queryType == EXPORT){
        if (tableCatalogue.isTable(parsedQuery.exportRelationName))
        {
            cout << "SEMANTIC PARSE of EXPORT DONE" << endl;
            return true;
        }
        
        cout << "SEMANTIC ERROR: No such TABLE exists" << endl;
    }
   
    else if (parsedQuery.queryType == EXPORT_MATRIX){
        if (matrixCatalogue.isMatrix(parsedQuery.loadRelationName))
        {
            cout << "SEMANTIC PARSE of EXPORT DONE" << endl;
            return true;
        }
        cout << "SEMANTIC ERROR: No such MATRIX exists" << endl;
        }
    // cout << "SEMANTIC ERROR: No such relation exists" << endl;
    return false;
}
// void executeEXPORT()
// {
//     logger.log("executeEXPORT");
//     Table* table = tableCatalogue.getTable(parsedQuery.exportRelationName);
//     table->makePermanent();
//     return;
// }

void executeEXPORT()
{
    logger.log("executeEXPORT");

    if (parsedQuery.queryType == EXPORT)
    {
        Table* table = tableCatalogue.getTable(parsedQuery.exportRelationName);
        if (table)
        {
            table->makePermanent();
            cout << "Exported table: " << parsedQuery.exportRelationName << endl;
        }
        else
        {
            cout << "EXECUTION ERROR: Table not found" << endl;
        }
    }
    else if (parsedQuery.queryType == EXPORT_MATRIX)
    {
        Matrix* matrix = matrixCatalogue.getMatrix(parsedQuery.loadRelationName);
        if (matrix)
        {
            matrix->makePermanent(); // Ensure this function is implemented in Matrix class
            cout << "Exported matrix: " << parsedQuery.loadRelationName << endl;
        }
        else
        {
            cout << "EXECUTION ERROR: Matrix not found" << endl;
        }
    }
}
