#include"semanticParser.h"

void executeCommand();

void executeCLEAR();
void executeCROSS();
void executeDISTINCT();
void executeEXPORT();
void executeINDEX();
void executeJOIN();
void executeLIST();
void executeLOAD();
void executePRINT();
void executePROJECTION();
void executeRENAME();
void executeSELECTION();
void executeSEARCH();
void executeINSERT();
void executeSORT();
void executeKWAYSORT();
void executeKWAYSORT();
void executeORDERBY();
void executeGROUPBY();
void executeSOURCE();
void executeROTATE();
void executeCROSSTRANSPOSE();
void executeCHECKANTISYM();
void executeUPDATE();
void executeDELETE();
bool evaluateBinOp(int value1, int value2, BinaryOperator binaryOperator);
void printRowCount(int rowCount);