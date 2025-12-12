# Project Phase-2 Report  
**TeamID: 35**  

## WORKING OF EACH COMMAND:

### SORT

**Syntax:**  
`SORT 〈table-name〉 BY 〈col1〉, 〈col2〉, 〈col3〉 IN 〈ASC|DESC〉, 〈ASC|DESC〉, 〈ASC|DESC〉`

**Logic:**  
- Load `k` (10) blocks at a time into memory. Sort each chunk based on multiple columns. Write sorted chunks back to disk as subfiles.  
- Keep track of start and end page indices for each sorted subfile.  
- Use a priority queue to merge sorted subfiles. Load the first row of each subfile into the queue. Extract the smallest row, write it to the final sorted table, and load more rows as needed.  
- **Perform merging in two passes:**  
  - **First pass:** Merge initial subfiles into intermediate sorted files.  
  - **Second pass:** Merge intermediate files into the fully sorted table.  
- Store the fully sorted table and delete temporary files.
- Did everything using a 3D vector buffer of buffer size.

---

### ORDER BY

**Syntax:**  
`Result-table <- ORDER BY attribute-name ASC|DESC ON table-name`

**Logic:**  
- Retrieves the table to be sorted from `tableCatalogue`. Creates a new result table (`resultTable`) where the sorted data will be stored.  
- Splits the table into chunks of `(k-1)` blocks each (`buffer size k=10`, so `k-1=9`).  
- Loads each chunk into memory, sorts it in-memory, and writes it back to disk as a sorted subfile. Stores the start and end page indices of each sorted subfile.  
- Uses a priority queue (min-heap) to merge multiple sorted subfiles efficiently. Loads the first row from each subfile into the priority queue.  
- Extracts the smallest row, writes it to the result table, and loads new rows as needed. If a subfile runs out of rows, read the next page of that subfile.  
- **Merging is done in 2 passes.**  
- Writes the completely sorted table to `parsedQuery.sortResultRelationName`. Cleans up intermediate files.
- Used only buffer as main variable, like in sort.

---

### GROUP BY

**Syntax:**  
`Result <- GROUP BY DepartmentID FROM EMPLOYEE HAVING AVG(Salary) > 50000 RETURN MAX(Salary)`

**Logic:**  
- Fetches the input table and creates a new result table to store grouped data. If sorting is required, it calls `executeKWAYSORT()` to sort the table by the `GROUP BY` column.  
- Reads the sorted table page by page (block-wise) using a buffer of size `10`.  
- Uses a map (`groupAggregates`) to store group-wise aggregates (`count, sum, max, min`, etc.). Iterates over the rows and updates aggregates for each unique `GROUP BY` value.  
- Checks if the computed `HAVING` aggregate satisfies the `HAVING` condition (`<, >, <=, >=, ==`). If the condition is met, the group result is stored in the result table.  
- Converts grouped results into blocks (pages) and stores them. Inserts the result table into the table catalog.
- Used buffer only as the main variable like in sort and order by.

---

### PARTITION HASH JOIN

**Syntax:**  
`Result-table <- JOIN table1, table2 ON col1, col2`

**Logic:**  
For the `JOIN` operation, a **Two Pass Hash Join Algorithm** has been used. The algorithm is divided into two main phases:

#### **Partitioning Phase**
- The goal of this phase is to partition both tables based on a hash function so that matching keys are in the same partition.  
- A hash function is applied to the join column values to distribute rows into `PRIME_HASH_MOD (=103)` partitions.  
- A cursor iterates over the left table (`table1`, also the function calling table).  
- Each row's join key (`col1`) is hashed to determine the partition. Rows are added to their corresponding partition in `leftPartitions`.  
- The right table is processed similarly in `rightPartitions`.  
- Each partition is stored as a separate page in disk storage using `bufferManager.writePage`.  

#### **Join Phase**
- In this phase, matching rows from the left and right table partitions are joined.  
- The algorithm iterates through all partitions:  
  - If the left partition exists, it is loaded from disk.  
  - A hash table is created using the left partition rows. Each row's key (`col1`) is used as a hash table entry.  
  - If the right partition exists, it is loaded.  
  - For each row in the right partition, the key (`col2`) is checked in `hashTable`.  
  - If a match is found, a joined row is created by concatenating the left and right rows and stored in the `resultBuffer`.  
  - Once `resultBuffer` reaches `maxRowsPerBlock`, it is written to disk in the `resultTable`.  

#### **Edge Cases**
- If no matches are found, a single row with `-1` values is stored to indicate an empty result.  
- Since partitions are written to disk, the algorithm can handle large datasets that don't fit in memory.  

---

## Contribution
- **Partition Hash Join** - Bhumika Joshi  
- **GROUP BY, ORDER BY, SORT** - R. Shaanal, Renu Sree Vyshnavi  
