#include "global.h"

bool syntacticParse()
{
    logger.log("syntacticParse");
    string possibleQueryType = tokenizedQuery[0];

    if (tokenizedQuery.size() < 2)
    {
        cout << "SYNTAX ERROR 1" << endl;
        return false;
    }

    if (possibleQueryType == "CLEAR")
        return syntacticParseCLEAR();
    else if (possibleQueryType == "INDEX")
        return syntacticParseINDEX();
    else if (possibleQueryType == "LIST")
        return syntacticParseLIST();
    else if (possibleQueryType == "LOAD")
        return syntacticParseLOAD();
    else if (possibleQueryType == "PRINT")
        return syntacticParsePRINT();
    else if (possibleQueryType == "RENAME")
        return syntacticParseRENAME();
    else if(possibleQueryType == "EXPORT")
        return syntacticParseEXPORT();
    else if(possibleQueryType == "SOURCE")
        return syntacticParseSOURCE();
    else if(possibleQueryType == "ROTATE")
        return syntacticParseROTATE();
    else if(possibleQueryType == "CROSSTRANSPOSE")
        return syntacticParseCROSSTRANSPOSE();
    else if(possibleQueryType == "CHECKANTISYM")
        return syntacticParseCHECKANTISYM();
    else if(possibleQueryType == "SORT")
        return syntacticParseKWAYSORT();
    else if (possibleQueryType == "INSERT")
        return syntacticParseINSERT();
    else if (possibleQueryType == "UPDATE")
        return syntacticParseUPDATE();
    else if (possibleQueryType == "DELETE")
        return syntacticParseDELETE();
    else
    {
        string resultantRelationName = possibleQueryType;
        if (tokenizedQuery[1] != "<-" || tokenizedQuery.size() < 3)
        {
            cout << "SYNTAX ERROR 2" << endl;
            return false;
        }
        possibleQueryType = tokenizedQuery[2];
        if (possibleQueryType == "PROJECT")
            return syntacticParsePROJECTION();
        else if (possibleQueryType == "SELECT")
            return syntacticParseSELECTION();
        else if (possibleQueryType == "JOIN")
            return syntacticParseJOIN();
        else if (possibleQueryType == "CROSS")
            return syntacticParseCROSS();
        else if (possibleQueryType == "DISTINCT")
            return syntacticParseDISTINCT();
        else if (possibleQueryType == "SEARCH")
            return syntacticParseSEARCH();
        else if (possibleQueryType == "SORT")
            return syntacticParseSORT();
        else if (possibleQueryType == "ORDER")
            return syntacticParseORDERBY();
        else if (possibleQueryType == "GROUP")
            return syntacticParseGROUPBY();
       
        else
        {
            cout << "SYNTAX ERROR 3" << endl;
            return false;
        }
    }
    return false;
}

ParsedQuery::ParsedQuery()
{
}

void ParsedQuery::clear()
{
    logger.log("ParseQuery::clear");
    this->queryType = UNDETERMINED;

    this->clearRelationName = "";

    this->crossResultRelationName = "";
    this->crossFirstRelationName = "";
    this->crossSecondRelationName = "";

    this->distinctResultRelationName = "";
    this->distinctRelationName = "";

    this->exportRelationName = "";

    this->indexingStrategy = NOTHING;
    this->indexColumnName = "";
    this->indexRelationName = "";

    this->joinBinaryOperator = NO_BINOP_CLAUSE;
    this->joinResultRelationName = "";
    this->joinFirstRelationName = "";
    this->joinSecondRelationName = "";
    this->joinFirstColumnName = "";
    this->joinSecondColumnName = "";

    this->loadRelationName = "";

    this->printRelationName = "";

    this->projectionResultRelationName = "";
    this->projectionColumnList.clear();
    this->projectionRelationName = "";

    this->renameFromColumnName = "";
    this->renameToColumnName = "";
    this->renameRelationName = "";

    this->selectType = NO_SELECT_CLAUSE;
    this->selectionBinaryOperator = NO_BINOP_CLAUSE;
    this->selectionResultRelationName = "";
    this->selectionRelationName = "";
    this->selectionFirstColumnName = "";
    this->selectionSecondColumnName = "";
    this->selectionIntLiteral = 0;

    this->searchBinaryOperator = NO_BINOP_CLAUSE;
    this->binop = "";
    this->searchResultRelationName = "";
    this->searchRelationName = "";
    this->searchColumnName = "";
    this->searchWhereValue = 0;
    
    this->updateTableName= "";
    this->updateColumnName_where = "";
    this->updateOperatorType_where = NO_BINOP_CLAUSE;
    this->updateValue_where = 0;
    this->updateSetColumnName = "";

    this->insertRelationName = "";
    this->insertColumnNames.clear();
    this->insertValues.clear();

    this->sortingStrategy = NO_SORT_CLAUSE;
    this->sortResultRelationName = "";
    this->sortColumnName = "";
    this->sortRelationName = "";

    this->sortColumnNames.clear();       
    this->sortingStrategies.clear();

    this->groupbyResultRelationName = "";
    this->groupbyRelationName = "";
    this->groupbyColumnName = "";
    this->groupbyHavingColumnName = ""; 
    this->groupbyHavingAggrFunc = NO_FUNC_CLAUSE;
    this->groupbyBinaryOperator = NO_BINOP_CLAUSE;
    this->groupbyHavingValue = "";
    this->groupbyReturnAggrFunc = NO_FUNC_CLAUSE;
    this->groupbyReturnColumnName = ""; 

    this->sourceFileName = "";

    this->rotateMatrixName = "";

    this->crosstransposeMatrix1Name = "";
    this->crosstransposeMatrix2Name = "";

    this->checkantisymMatrixName = "";
    this->loadMatrixName = "";

    this->deleteTableName = "";
    this->deleteColumnName_where = "";
    this->deleteOperatorType_where = NO_BINOP_CLAUSE;
    this->deleteValue_where = 0;
}

/**
 * @brief Checks to see if source file exists. Called when LOAD command is
 * invoked.
 *
 * @param tableName 
 * @return true 
 * @return false 
 */
bool isFileExists(string tableName)
{
    string fileName = "../data/" + tableName + ".csv";
    struct stat buffer;
    return (stat(fileName.c_str(), &buffer) == 0);
}

/**
 * @brief Checks to see if source file exists. Called when SOURCE command is
 * invoked.
 *
 * @param tableName 
 * @return true 
 * @return false 
 */
bool isQueryFile(string fileName){
    fileName = "../data/" + fileName + ".ra";
    struct stat buffer;
    return (stat(fileName.c_str(), &buffer) == 0);
}
