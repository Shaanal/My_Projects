#include "tableCatalogue.h"
#include "matrixCatalogue.h"
using namespace std;

enum QueryType
{
    CLEAR,
    CROSS,
    DISTINCT,
    EXPORT,
    EXPORT_MATRIX,
    INDEX,
    JOIN,
    LIST,
    LOAD,
    LOAD_MATRIX,
    PRINT,
    PRINT_MATRIX,
    PROJECTION,
    RENAME,
    SELECTION,
    SEARCH,
    INSERT,
    SORT,
    KWAYSORT,
    ORDERBY,
    GROUPBY,
    SOURCE,
    ROTATE,
    CROSSTRANSPOSE,
    CHECKANTISYM,
    LOADMATRIX,
    UNDETERMINED,
    UPDATE,
    DELETE
};

enum BinaryOperator
{
    LESS_THAN,
    GREATER_THAN,
    LEQ,
    GEQ,
    EQUAL,
    NOT_EQUAL,
    NO_BINOP_CLAUSE
};

enum FunctionType
{
    SUM,
    AVG,
    MAX,
    MIN,
    COUNT,
    NO_FUNC_CLAUSE
};

enum SortingStrategy
{
    ASC,
    DESC,
    NO_SORT_CLAUSE
};

enum SelectType
{
    COLUMN,
    INT_LITERAL,
    NO_SELECT_CLAUSE
};

class ParsedQuery
{

public:
    QueryType queryType = UNDETERMINED;

    string clearRelationName = "";

    string crossResultRelationName = "";
    string crossFirstRelationName = "";
    string crossSecondRelationName = "";

    string distinctResultRelationName = "";
    string distinctRelationName = "";

    string exportRelationName = "";

    IndexingStrategy indexingStrategy = NOTHING;
    string indexColumnName = "";
    string indexRelationName = "";

    BinaryOperator joinBinaryOperator = NO_BINOP_CLAUSE;
    string joinResultRelationName = "";
    string joinFirstRelationName = "";
    string joinSecondRelationName = "";
    string joinFirstColumnName = "";
    string joinSecondColumnName = "";

    string loadRelationName = "";

    string printRelationName = "";

    string projectionResultRelationName = "";
    vector<string> projectionColumnList;
    string projectionRelationName = "";

    string renameFromColumnName = "";
    string renameToColumnName = "";
    string renameRelationName = "";

    SelectType selectType = NO_SELECT_CLAUSE;
    BinaryOperator selectionBinaryOperator = NO_BINOP_CLAUSE;
    string selectionResultRelationName = "";
    string selectionRelationName = "";
    string selectionFirstColumnName = "";
    string selectionSecondColumnName = "";
    int selectionIntLiteral = 0;

    BinaryOperator searchBinaryOperator = NO_BINOP_CLAUSE;
    string searchResultRelationName = "";
    string searchRelationName = "";
    string searchColumnName = "";
    int searchWhereValue = 0;

    string updateTableName = "";
    string updateColumnName_where = "";
    BinaryOperator updateOperatorType_where = NO_BINOP_CLAUSE;
    int updateValue_where = 0;
    string updateSetColumnName = "";
    int updateSetValue = 0;

    string insertRelationName = "";
    vector<string> insertColumnNames;
    vector<int> insertValues;

    SortingStrategy sortingStrategy = NO_SORT_CLAUSE;
    string sortResultRelationName = "";
    string sortColumnName = "";
    string sortRelationName = "";

    vector<string> sortColumnNames;       
    vector<SortingStrategy> sortingStrategies;

    string groupbyResultRelationName = "";
    string groupbyRelationName = "";
    string groupbyColumnName = "";
    FunctionType groupbyHavingAggrFunc = NO_FUNC_CLAUSE;
    string groupbyHavingColumnName = "";
    BinaryOperator groupbyBinaryOperator = NO_BINOP_CLAUSE;
    string groupbyHavingValue = "";
    FunctionType groupbyReturnAggrFunc = NO_FUNC_CLAUSE;
    string groupbyReturnColumnName = "";

    string sourceFileName = "";

    string rotateMatrixName = "";

    string crosstransposeMatrix1Name = "";
    string crosstransposeMatrix2Name = "";

    string checkantisymMatrixName = "";

    string loadMatrixName = "";

    string deleteTableName = "";
    string deleteColumnName_where = "";
    BinaryOperator deleteOperatorType_where = NO_BINOP_CLAUSE;
    int deleteValue_where = 0;

    string binop = "";

    ParsedQuery();
    void clear();
};

bool syntacticParse();
bool syntacticParseCLEAR();
bool syntacticParseCROSS();
bool syntacticParseDISTINCT();
bool syntacticParseEXPORT();
bool syntacticParseINDEX();
bool syntacticParseJOIN();
bool syntacticParseLIST();
bool syntacticParseLOAD();
bool syntacticParsePRINT();
bool syntacticParsePROJECTION();
bool syntacticParseRENAME();
bool syntacticParseSELECTION();
bool syntacticParseSORT();
bool syntacticParseSEARCH();
bool syntacticParseINSERT();
bool syntacticParseKWAYSORT();
bool syntacticParseORDERBY();
bool syntacticParseGROUPBY();
bool syntacticParseSOURCE();
bool syntacticParseROTATE();
bool syntacticParseCROSSTRANSPOSE();
bool syntacticParseCHECKANTISYM();
bool syntacticParseUPDATE();
bool syntacticParseDELETE();
bool isFileExists(string tableName);
bool isQueryFile(string fileName);
