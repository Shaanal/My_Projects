#include "global.h"
/**
 * @brief 
 * SYNTAX: LOAD relation_name
 */
// bool syntacticParseLOAD()
// {
//     logger.log("syntacticParseLOAD");
//     if (tokenizedQuery.size() != 2)
//     {
//         cout << "SYNTAX ERROR" << endl;
//         return false;
//     }
//     parsedQuery.queryType = LOAD;
//     parsedQuery.loadRelationName = tokenizedQuery[1];
//     return true;
// }

bool syntacticParseLOAD()
{
    logger.log("syntacticParseLOAD");

    if (tokenizedQuery.size() < 2 || tokenizedQuery.size() > 3)
    {
        cout << "SYNTAX ERROR" << endl;
        return false;
    }

    if (tokenizedQuery.size() == 3 && tokenizedQuery[1] == "MATRIX")
    {
        // Handling matrix loading
        parsedQuery.queryType = LOAD_MATRIX;
        parsedQuery.loadRelationName = tokenizedQuery[2];
        cout << "SYNTACTIC PARSE of load DONE" << endl;
    }
    else if (tokenizedQuery.size() == 2)
    {
        // Handling table loading (default behavior)
        parsedQuery.queryType = LOAD;
        parsedQuery.loadRelationName = tokenizedQuery[1];
    }
    else
    {
        cout << "SYNTAX ERROR" << endl;
        return false;
    }

    return true;
}


// bool semanticParseLOAD()
// {
//     logger.log("semanticParseLOAD");
//     if (tableCatalogue.isTable(parsedQuery.loadRelationName))
//     {
//         cout << "SEMANTIC ERROR: Relation already exists" << endl;
//         return false;
//     }

//     if (!isFileExists(parsedQuery.loadRelationName))
//     {
//         cout << "SEMANTIC ERROR: Data file doesn't exist" << endl;
//         return false;
//     }
//     return true;
// }

bool semanticParseLOAD()
{
    logger.log("semanticParseLOAD");

    if (parsedQuery.queryType == LOAD)
    {
        // Handling table loading
        if (tableCatalogue.isTable(parsedQuery.loadRelationName))
        {
            cout << "SEMANTIC ERROR: Table already exists" << endl;
            return false;
        }
    }
    else if (parsedQuery.queryType == LOAD_MATRIX)
    {
        // Handling matrix loading
        if (matrixCatalogue.isMatrix(parsedQuery.loadRelationName))
        {
            cout << "SEMANTIC ERROR: Matrix already exists" << endl;
            return false;
        }
    }
    else
    {
        cout << "SEMANTIC ERROR: Invalid query type for LOAD" << endl;
        return false;
    }

    // Checking if the file exists
    if (!isFileExists(parsedQuery.loadRelationName))
    {
        cout << "SEMANTIC ERROR: Data file doesn't exist" << endl;
        return false;
    }
    cout << "SEMANTIC PARSE of load DONE" << endl;

    return true;
}



// void executeLOAD()
// {
//     logger.log("executeLOAD");

//     Table *table = new Table(parsedQuery.loadRelationName);
//     if (table->load())
//     {
//         tableCatalogue.insertTable(table);
//         cout << "Loaded Table. Column Count: " << table->columnCount << " Row Count: " << table->rowCount << endl;
//     }
//     return;
// }
void executeLOAD()
{
    logger.log("executeLOAD");
    cout << "INSIDE EXECUTE of LOAD" << endl;
    if (parsedQuery.queryType == LOAD)
    {
        // Handling table loading
        Table *table = new Table(parsedQuery.loadRelationName);
        if (table->load())
        {
            tableCatalogue.insertTable(table);
            cout << "Loaded Table. Column Count: " << table->columnCount << " Row Count: " << table->rowCount << endl;
        }
    }
    else if (parsedQuery.queryType == LOAD_MATRIX)
    {
        cout << "INSIDE EXECUTE IF of LOAD" << endl;
        // Handling matrix loading
        Matrix *matrix = new Matrix(parsedQuery.loadRelationName);
        if (matrix->load())
        {
            matrixCatalogue.insertMatrix(matrix);
            cout << "Loaded Matrix. Size: " << matrix->mat_size << "x" << matrix->mat_size << endl;
        }
    }
    return;
}
