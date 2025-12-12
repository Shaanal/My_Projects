#include "global.h"
/**
 * @brief 
 * SYNTAX: CROSSTRANSPOSE matrix_name1 matrix_name2
 */

bool syntacticParseCROSSTRANSPOSE(){
    logger.log("syntacticParseCROSSTRANSPOSE");
    if (tokenizedQuery.size() != 3)
    {
        cout << "SYNTAX ERROR" << endl;
        return false;
    }
    parsedQuery.queryType = CROSSTRANSPOSE;
    parsedQuery.crosstransposeMatrix1Name = tokenizedQuery[1];
    parsedQuery.crosstransposeMatrix2Name = tokenizedQuery[2];
    return true;
}

bool semanticParseCROSSTRANSPOSE(){
    logger.log("semanticParseCROSSTRANSPOSE");
    if (!matrixCatalogue.isMatrix(parsedQuery.crosstransposeMatrix1Name))
    {
        cout << "SEMANTIC ERROR: Matrix1 doesn't exists\n";
        return false;
    }
    if (!matrixCatalogue.isMatrix(parsedQuery.crosstransposeMatrix2Name))
    {
        cout << "SEMANTIC ERROR: Matrix2 doesn't exists\n";
        return false;
    }
    
    return true;
}

void executeCROSSTRANSPOSE(){
    logger.log("executeCROSSTRANSPOSE");
    Matrix *matrix1 = matrixCatalogue.getMatrix(parsedQuery.crosstransposeMatrix1Name);
    Matrix *matrix2 = matrixCatalogue.getMatrix(parsedQuery.crosstransposeMatrix2Name);
    matrix1->crossTranspose(matrix2);
}