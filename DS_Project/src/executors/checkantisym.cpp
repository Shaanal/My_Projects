#include "global.h"
/**
 * @brief 
 * SYNTAX: CHECKANTISYM matrix_name
 */

bool syntacticParseCHECKANTISYM(){
    logger.log("syntacticParseCHECKANTISYM");
    if (tokenizedQuery.size() != 2)
    {
        cout << "SYNTAX ERROR" << endl;
        return false;
    }
    parsedQuery.queryType = CHECKANTISYM;
    parsedQuery.checkantisymMatrixName = tokenizedQuery[1];
    return true;
}

bool semanticParseCHECKANTISYM(){
    logger.log("semanticParseCHECKANTISYM");
    if (!matrixCatalogue.isMatrix(parsedQuery.checkantisymMatrixName))
    {
        cout << "SEMANTIC ERROR: Matrix1 doesn't exists\n";
        return false;
    }
    
    return true;
}

void executeCHECKANTISYM(){
    logger.log("executeCHECKANTISYM");
    Matrix *matrix = matrixCatalogue.getMatrix(parsedQuery.checkantisymMatrixName);
    bool result = matrix->checkAntiSym();
    if(result == true){
        cout<<"True";
    }
    else{
        cout<<"False";
    }
}