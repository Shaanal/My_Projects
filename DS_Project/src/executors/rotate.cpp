#include "global.h"
/**
 * @brief 
 * SYNTAX: ROTATE relation_name
 */

bool syntacticParseROTATE(){
    logger.log("syntacticParseROTATE");
    if (tokenizedQuery.size() != 2)
    {
        cout << "SYNTAX ERROR" << endl;
        return false;
    }
    parsedQuery.queryType = ROTATE;
    parsedQuery.rotateMatrixName = tokenizedQuery[1];
    return true;
}

bool semanticParseROTATE(){
    logger.log("semanticParseLOAD");
    if (!matrixCatalogue.isMatrix(parsedQuery.rotateMatrixName))
    {
        cout << "SEMANTIC ERROR: Matrix doesn't exists\n";
        return false;
    }
    
    return true;
}

void executeROTATE(){
    logger.log("executeROTATE");
    Matrix *matrix = matrixCatalogue.getMatrix(parsedQuery.rotateMatrixName);
    matrix->rotate();
}