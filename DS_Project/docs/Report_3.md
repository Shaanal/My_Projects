# Project Phase-3 Report - TeamID: 35

## INDEXING USED: LSM (Log-Structured Merge-Tree)

### Why LSM?

We chose the LSM Tree indexing structure for the following reasons:

*   **Efficient for Write-Heavy Workloads:** LSM trees are optimized for high write throughput, making them suitable for databases with potentially frequent INSERT, UPDATE, and DELETE operations (though our implementation focuses on using it for SEARCH). Instead of modifying data in-place like B-trees, LSM trees batch writes in memory (`memtable`) before flushing them sequentially to disk as SSTables, reducing random I/O which is beneficial under memory constraints.
*   **Handles Large Datasets Efficiently:** Since the problem states that tables may not fit in main memory, LSM’s tiered storage (memory + multiple disk levels/SSTables) helps manage large datasets. Data is stored in sorted runs (SSTables) on disk.
*   **Disk-Based Storage Suitability:** LSM minimizes random disk seeks by sequentially writing data in SSTables, which is generally faster than the random writes often required by B-tree page splits/updates, especially when only 10 blocks can be in memory.
*   **Supports Lookups for SEARCH Queries:** While LSM trees can have higher read latency than B-trees for point lookups (potentially checking memtable + multiple SSTables), our implementation focuses on the `SEARCH` command. For range queries (like `math >= 30`), the sorted nature of SSTables allows for efficient scanning once the relevant files/ranges are identified. *Note: Our current implementation scans all SSTables; optimizations like Bloom filters were not implemented.*

### Why Not B-Tree?

*   B-trees typically involve in-place updates, which can lead to higher write amplification (more random disk I/O) compared to LSM's sequential writes, potentially less efficient for very large tables under strict memory limits.
*   While B-trees offer excellent read performance, LSM trees can offer competitive performance for write-heavy scenarios and manage disk I/O differently, which seemed advantageous given the constraints.
*   *Initial Consideration:* We considered B+ Trees but ultimately selected LSM based on its write handling characteristics and sequential disk access patterns, anticipating potential benefits for larger-than-memory tables.

## WORKING OF EACH COMMAND (with LSM Index)

### SEARCH

*   **Syntax:** `res_table <- SEARCH FROM table_name WHERE condition`
*   **Logic:**
    1.  **Index Initialization/Loading:** The LSM Tree index is created/loaded for the column specified in the `WHERE` clause. This involves initializing an in-memory `memtable` (a sorted map of `key -> vector<rowIndex>`) and potentially loading metadata about existing disk-based `SSTable` files. If the index doesn't exist, it's built by scanning the entire source table.
    2.  **Condition Evaluation (Memtable):** The `memtable` is searched first. For each key stored, the `WHERE` condition (e.g., `>`, `<`, `==`) is evaluated against the query's value. If a key matches, its associated row indices are collected.
    3.  **Condition Evaluation (SSTables):** Each relevant `SSTable` file on disk is sequentially scanned. Keys within the SSTable are read and compared against the `WHERE` condition. Matching keys lead to their associated row indices being added to the results. *(Note: Our implementation scans all SSTables.)*
    4.  **Row Retrieval:** The unique set of collected row indices (from memtable and SSTables) is used to fetch the complete corresponding data rows from the original table's data pages using `table->getRow()`. This involves potentially random access to table data pages managed by the `BufferManager`.
    5.  **Result Materialization:** A new temporary table is created with the same schema as the source table. The fetched data rows are written (buffered into pages) to this new table using `bufferManager.writePage()`. The result table's metadata (row count, block count) is updated.

### INSERT

*   **Syntax:** `INSERT INTO table_name VALUES value1, value2,...` or `INSERT INTO table_name FROM RELATION relation_name`
*   **Logic (Interaction with Index):**
    1.  **Direct Table Insertion:** The new row data is first inserted directly into the main table's data pages using `table->insertRow()`. *This step happens independently of the index.*
    2.  **Memtable Update:** After the row is inserted into the table and its final `rowIndex` is determined, the LSM index's `memtable` is updated. The value from the indexed column (`key`) and the `rowIndex` are added to the in-memory map.
    3.  **Sorted In-Memory:** The `memtable` (often a `std::map` or similar) keeps the keys sorted implicitly or explicitly.
    4.  **Flush to Disk (SSTable):** When the `memtable` reaches a predefined size limit (`MEMTABLE_LIMIT`), its contents are written sequentially to a new, immutable `SSTable` file on disk. The `memtable` is then cleared.
    5.  **Write Optimization:** Individual inserts only affect the in-memory `memtable` until a flush is triggered, minimizing immediate disk I/O per insert. Index maintenance (like merging SSTables later, known as compaction) happens separately.

### UPDATE

*   **Syntax:** `UPDATE table_name SET col_name1 = value1, ... WHERE col_name2 bin_op value2`
*   **Logic (Interaction with Index):**
    1.  **Index Initialization/Loading:** The LSM Tree index is loaded/created for the column specified in the `WHERE` clause (`col_name2`).
    2.  **Identify Rows via Index:** The `rangeSearchIndex()` method is called on the index. This searches the `memtable` and scans relevant `SSTable` files based on the `WHERE` condition (`col_name2 bin_op value2`), returning only the `rowIndex`(es) of the rows that match.
    3.  **Row Modification:** For each identified `rowIndex`:
        *   The `LSMTreeIndex::update()` method (or potentially direct table access after getting indices) fetches the target row from the table using `table->getRow(rowIndex)`.
        *   It then calls `table->updateRow(rowIndex, col_name1, value1, ...)` to modify the specified column(s) with the new value(s) directly within the table's data pages.
    4.  **Index Maintenance (Crucial & Potentially Implicit):**
        *   **If the indexed column (`col_name2`) is updated:** The old key entry associated with the `rowIndex` must be effectively removed from the index, and a new entry for the *new key value* and the same `rowIndex` must be added (typically via the `memtable`).
        *   **If a non-indexed column (`col_name1`) is updated:** The index (which maps `col_name2` values) usually doesn't need direct changes, as the `rowIndex` remains the same.
        *   *Note:* The provided `LSMTreeIndex::update` stub seems to only delegate to `table->updateRow`. A complete implementation needs to handle the index consistency logic, especially when the indexed key itself changes, potentially by treating it as a delete-then-insert operation within the index.

### DELETE

*   **Syntax:** `DELETE FROM table_name WHERE col_name bin_op value`
*   **Logic (Interaction with Index):**
    1.  **Identify Rows via Index:** The LSM index for the `WHERE` clause column (`col_name`) is used. The `rangeSearchIndex()` method searches the `memtable` and scans `SSTable` files to efficiently find all `rowIndex`(es) matching the condition.
    2.  **Logical Deletion (Tombstones):** For each identified `rowIndex`:
        *   The corresponding key is found in the `memtable`. A special marker (a "tombstone") might be added to the `memtable` associated with this key/rowIndex, indicating it's deleted (instead of physically removing the entry immediately). Alternatively, as shown in the code, the entry might be directly removed from the `memtable`.
        *   The `table->deleteRow(rowIndex)` method is called to handle the physical deletion or marking within the main table's data pages.
    3.  **Deferred Physical Removal from Index:** The tombstone markers (if used) or the absence of the key in newer structures effectively hides the deleted data during reads. Actual removal of deleted entries from the *index's disk structures* occurs later during the `SSTable` compaction process, where SSTables are merged, and tombstoned/obsolete entries are discarded. Direct removal from SSTables is not possible as they are immutable.
    4.  **Consistency:** This approach ensures that lookups correctly reflect the deletion (by encountering a tombstone or not finding the key in newer levels) while deferring the cost of modifying the disk-based index structures.

## Contribution:


