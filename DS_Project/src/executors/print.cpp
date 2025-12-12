#include "global.h"
/**
 * @brief 
 * SYNTAX: PRINT relation_name
 */
// bool syntacticParsePRINT()
// {
//     logger.log("syntacticParsePRINT");
//     if (tokenizedQuery.size() != 2)
//     {
//         cout << "SYNTAX ERROR" << endl;
//         return false;
//     }
//     parsedQuery.queryType = PRINT;
//     parsedQuery.printRelationName = tokenizedQuery[1];
//     return true;
// }
bool syntacticParsePRINT()
{
    logger.log("syntacticParsePRINT");

    if (tokenizedQuery.size() == 2)  // Case: PRINT <table>
    {
        parsedQuery.queryType = PRINT;
        parsedQuery.printRelationName = tokenizedQuery[1];
        return true;
    }
    else if (tokenizedQuery.size() == 3 && tokenizedQuery[1] == "MATRIX") // Case: PRINT MATRIX <matrix>
    {
        parsedQuery.queryType = PRINT_MATRIX;
        parsedQuery.printRelationName = tokenizedQuery[2]; // Store matrix name
        cout << "SYNTACTIC PARSE of print DONE" << endl;
        return true;
    }
    else
    {
        cout << "SYNTAX ERROR" << endl;
        return false;
    }
}


// bool semanticParsePRINT()
// {
//     logger.log("semanticParsePRINT");
//     if (!tableCatalogue.isTable(parsedQuery.printRelationName))
//     {
//         cout << "SEMANTIC ERROR: Relation doesn't exist" << endl;
//         return false;
//     }
//     return true;
// }
bool semanticParsePRINT()
{
    logger.log("semanticParsePRINT");

    if (parsedQuery.queryType == PRINT) // Case: PRINT <table>
    {
        if (!tableCatalogue.isTable(parsedQuery.printRelationName))
        {
            cout << "SEMANTIC ERROR: Table doesn't exist" << endl;
            return false;
        }
    }
    else if (parsedQuery.queryType == PRINT_MATRIX) // Case: PRINT MATRIX <matrix>
    {
        if (!matrixCatalogue.isMatrix(parsedQuery.printRelationName))
        {
            cout << "SEMANTIC ERROR: Matrix doesn't exist" << endl;
            return false;
        }
    }
    else
    {
        cout << "SEMANTIC ERROR: Invalid query type" << endl;
        return false;
    }
    cout << "SEMANTIC PARSE of print DONE" << endl;
    return true;
}


// void executePRINT()
// {
//     logger.log("executePRINT");
//     Table* table = tableCatalogue.getTable(parsedQuery.printRelationName);
//     table->print();
//     return;
// }

void executePRINT()
{
    logger.log("executePRINT");

    if (parsedQuery.queryType == PRINT)
    {
        if (tableCatalogue.isTable(parsedQuery.printRelationName))
        {
            Table* table = tableCatalogue.getTable(parsedQuery.printRelationName);
            table->print();
        }
        else
        {
            cout << "ERROR: Table does not exist." << endl;
        }
    }
    else if (parsedQuery.queryType == PRINT_MATRIX)
    {
        cout << "INSIDE EXECUTE of print" << endl;
        if (matrixCatalogue.isMatrix(parsedQuery.printRelationName))
        {
            Matrix* matrix = matrixCatalogue.getMatrix(parsedQuery.printRelationName);
            cout << "INSIDE EXECUTE IF of print" << endl;
            matrix->print();
        }
        else
        {
            cout << "ERROR: Matrix does not exist." << endl;
        }
    }
    else
    {
        cout << "ERROR: Invalid PRINT query type." << endl;
    }

    return;
}
