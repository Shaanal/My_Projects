#include "lsmIndex.h"
/**
 * @brief 
 * SYNTAX: INSERT INTO table_name ( col1 = val1, col2 = val2, col3 = val3 ... ) 
 */
bool syntacticParseINSERT()
{
    logger.log("syntacticParseINSERT");
    
    if (tokenizedQuery[0] != "INSERT" || tokenizedQuery[1] != "INTO" || tokenizedQuery[3] != "(")
    {
        cout << "SYNTAX ERROR" << endl;
        return false;
    }

    parsedQuery.queryType = INSERT;
    parsedQuery.insertRelationName = tokenizedQuery[2];

    auto bracketPosition = find(tokenizedQuery.begin(), tokenizedQuery.end(), "(");
    parsedQuery.insertColumnNames.clear();
    parsedQuery.insertValues.clear();

    regex numeric("[-]?[0-9]+");  // Regex to match integers

    // Start from the token after the "("
    for (auto it = bracketPosition + 1; it != tokenizedQuery.end(); ++it)
    {
        if (*it == ")")  // End of the column-value pair parsing
            break;

        if (*it == ",")  // Skip commas
            continue;

        string columnName = *it;  // Column name is expected here
        ++it;  // Move to the next token

        if (*it != "=")  // If "=" is not found, it's a syntax error
        {
            cout << "SYNTAX ERROR: Expected '=' after column name" << endl;
            return false;
        }

        ++it;  // Move to the value after "="

        if (it == tokenizedQuery.end())  // Check for value existence
        {
            cout << "SYNTAX ERROR: Missing value for column " << columnName << endl;
            return false;
        }

        string value = *it;  // Value can be numeric or string
        parsedQuery.insertColumnNames.push_back(columnName);

        // Check if the value is numeric
        if (regex_match(value, numeric))
        {
            parsedQuery.insertValues.push_back(stoi(value));  // Convert to integer if numeric
        }
        else
        {
            parsedQuery.insertValues.push_back(0);  // Set to 0 for non-numeric values (or handle strings separately)
        }

        ++it;  // Move to the next token for the next column-value pair
    }

    cout << "INSERT: SYNTACTIC PARSE done!" << endl;
    return true;
}

// bool syntacticParseINSERT()
// {
//     logger.log("syntacticParseINSERT");
//     if (tokenizedQuery[0] != "INSERT" || tokenizedQuery[1] != "INTO" || tokenizedQuery[3] != "(")
//     {
//         cout << "SYNTAX ERROR" << endl;
//         return false;
//     }

//     parsedQuery.queryType = INSERT;
//     parsedQuery.insertRelationName = tokenizedQuery[2];

//     auto bracketPosition = find(tokenizedQuery.begin(), tokenizedQuery.end(), "(");
//     parsedQuery.insertColumnNames.clear();
//     parsedQuery.insertValues.clear();

//     regex numeric("[-]?[0-9]+");
//     for (auto it = tokenizedQuery.begin() + 3; it != bracketPosition; ++it)
//     {
//         if (*it == ","){
//             parsedQuery.insertColumnNames.push_back(*(++it));
//             cout<<*it;
//         }
//         else if (*it == "=")
//         {
//             if(regex_match(*(++it), numeric))
//             {
//                 cout << "SYNTAX ERROR: VALUE ERROR" << endl;
//                 return false;
//             }
//             parsedQuery.insertValues.push_back(stoi(*(it)));
//         }
//         else if (*it == ")")
//             break;
//     } 
//     cout << "INSERT: SYNTACTIC PARSE done!" << endl;
//     return true;
// }

bool semanticParseINSERT()
{
    logger.log("semanticParseINSERT");

    if (!tableCatalogue.isTable(parsedQuery.insertRelationName))
    {
        cout << "SEMANTIC ERROR: Relation doesn't exist" << endl;
        return false;
    }

    for (string column : parsedQuery.insertColumnNames)
    {
        if (!tableCatalogue.isColumnFromTable(column, parsedQuery.insertRelationName))
        {
            cout << "SEMANTIC ERROR: Column " << column << " does not exist in table " << parsedQuery.sortRelationName << endl;
            return false;
        }
    }

    cout << "INSERT: SEMANTIC PARSE done!" << endl;
    return true;
}

// bool evaluateBinOp(int value1, int value2, BinaryOperator binaryOperator)
// {
//     switch (binaryOperator)
//     {
//     case LESS_THAN:
//         return (value1 < value2);
//     case GREATER_THAN:
//         return (value1 > value2);
//     case LEQ:
//         return (value1 <= value2);
//     case GEQ:
//         return (value1 >= value2);
//     case EQUAL:
//         return (value1 == value2);
//     case NOT_EQUAL:
//         return (value1 != value2);
//     default:
//         return false;
//     }
// }

void executeINSERT()
{
    logger.log("executeINSERT");

    // cout<<parsedQuery.insertColumnNames[0];

    Table* table = tableCatalogue.getTable(parsedQuery.insertRelationName);
    LSMTreeIndex index(table->tableName, table->columns[0]);
    index.insert(parsedQuery.insertColumnNames, parsedQuery.insertValues);
    // Table* resultantTable = new Table(parsedQuery.insertResultRelationName, table.columns);
    // Cursor cursor = table.getCursor();
    // vector<int> row = cursor.getNext();
    // int firstColumnIndex = table.getColumnIndex(parsedQuery.insertFirstColumnName);
    // int secondColumnIndex;
    // if (parsedQuery.selectType == COLUMN)
    //     secondColumnIndex = table.getColumnIndex(parsedQuery.insertSecondColumnName);
    // while (!row.empty())
    // {

    //     int value1 = row[firstColumnIndex];
    //     int value2;
    //     if (parsedQuery.selectType == INT_LITERAL)
    //         value2 = parsedQuery.insertIntLiteral;
    //     else
    //         value2 = row[secondColumnIndex];
    //     if (evaluateBinOp(value1, value2, parsedQuery.insertBinaryOperator))
    //         resultantTable->writeRow<int>(row);
    //     row = cursor.getNext();
    // }
    // if(resultantTable->blockify())
    //     tableCatalogue.insertTable(resultantTable);
    // else{
    //     cout<<"Empty Table"<<endl;
    //     resultantTable->unload();
    //     delete resultantTable;
    // }
    return;
}