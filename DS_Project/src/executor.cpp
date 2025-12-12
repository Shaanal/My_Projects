#include"global.h"

void executeCommand(){

    switch(parsedQuery.queryType){
        case CLEAR: executeCLEAR(); break;
        case CROSS: executeCROSS(); break;
        case DISTINCT: executeDISTINCT(); break;
        case EXPORT: executeEXPORT(); break;
        case EXPORT_MATRIX: executeEXPORT(); break;
        case INDEX: executeINDEX(); break;
        case JOIN: executeJOIN(); break;
        case LIST: executeLIST(); break;
        case LOAD: executeLOAD(); break;
        case LOAD_MATRIX:executeLOAD();break;
        case PRINT: executePRINT(); break;
        case PRINT_MATRIX: executePRINT(); break;
        case PROJECTION: executePROJECTION(); break;
        case RENAME: executeRENAME(); break;
        case SELECTION: executeSELECTION(); break;
        case SEARCH: executeSEARCH(); break;
        case INSERT: executeINSERT(); break;
        case SORT: executeSORT(); break;
        case KWAYSORT: executeKWAYSORT(); break;
        case ORDERBY: executeORDERBY(); break;
        case GROUPBY: executeGROUPBY(); break;
        case SOURCE: executeSOURCE(); break;
        case ROTATE: executeROTATE(); break;
        case CROSSTRANSPOSE: executeCROSSTRANSPOSE(); break;
        case CHECKANTISYM: executeCHECKANTISYM(); break;
        case UPDATE: executeUPDATE(); break;
        case DELETE: executeDELETE(); break;
        default: cout<<"PARSING ERROR"<<endl;
    }

    return;
}

void printRowCount(int rowCount){
    cout<<"\n\nRow Count: "<<rowCount<<endl;
    return;
}