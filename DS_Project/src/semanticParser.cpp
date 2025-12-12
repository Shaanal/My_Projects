#include"global.h"

bool semanticParse(){
    logger.log("semanticParse");
    switch(parsedQuery.queryType){
        case CLEAR: return semanticParseCLEAR();
        case CROSS: return semanticParseCROSS();
        case DISTINCT: return semanticParseDISTINCT();
        case EXPORT: return semanticParseEXPORT();
        case EXPORT_MATRIX: return semanticParseEXPORT();
        case INDEX: return semanticParseINDEX();
        case JOIN: return semanticParseJOIN();
        case LIST: return semanticParseLIST();
        case LOAD: return semanticParseLOAD();
        case LOAD_MATRIX: return semanticParseLOAD();
        case PRINT: return semanticParsePRINT();
        case PRINT_MATRIX: return semanticParsePRINT();
        case PROJECTION: return semanticParsePROJECTION();
        case RENAME: return semanticParseRENAME();
        case SELECTION: return semanticParseSELECTION();
        case SEARCH: return semanticParseSEARCH();
        case INSERT: return semanticParseINSERT();
        case SORT: return semanticParseSORT();
        case KWAYSORT: return semanticParseKWAYSORT();
        case ORDERBY: return semanticParseORDERBY();
        case GROUPBY: return semanticParseGROUPBY();
        case SOURCE: return semanticParseSOURCE();
        case ROTATE: return semanticParseROTATE();
        case CROSSTRANSPOSE: return semanticParseCROSSTRANSPOSE();
        case CHECKANTISYM: return semanticParseCHECKANTISYM();
        case UPDATE: return semanticParseUPDATE();
        case DELETE: return semanticParseDELETE();
        default: cout<<"SEMANTIC ERROR"<<endl;
    }

    return false;
}