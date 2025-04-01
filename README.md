# Ride-sharing-spark-streaming

This project demonstrates real-time ride-sharing analytics using **Apache Spark Structured Streaming**. The system ingests simulated ride data, processes it using Spark, and writes real-time analytics results to disk.

---

## Requirements
- Python 3.8+
- `pyspark` (install via `pip install pyspark`)
- `faker` (for generating random ride data: `pip install faker`)

---

## Project Structure
```
ride-sharing-spark-streaming/
├── src/
│   ├── task1_streaming_ingestion.py    # Ingest and parse real-time JSON data
│   ├── task2_driver_aggregations.py    # Driver-level aggregation (total fare, avg distance)
│   ├── task3_windowed_analytics.py     # Sliding window aggregation of fare amounts
├── data_generator.py                  # Simulates real-time ride data via socket
├── output/                            # Output data for each task
└── README.md                          # You're here
```

---

## Simulating Data: `data_generator.py`

This script creates a socket server on `localhost:9999` and sends simulated ride data in JSON format every second.

### Key Points:
- Uses Python's `socket` and `uuid` to create and send unique ride entries
- Timestamps are current system time
- Run this script before any Spark task

### Run:
```bash
python data_generator.py
```

---

## Task 1: Basic Streaming Ingestion and Parsing

### File: `task1_streaming_ingestion.py`

### Objective:
- Connect to the socket server (localhost:9999)
- Parse JSON ride events
- Save structured output to CSV

### Code Highlights:
- `spark.readStream.format("socket")`: Reads text stream from port 9999
- `from_json()`: Converts string to structured JSON
- `writeStream.format("csv")`: Writes to disk continuously in append mode

### Steps:
```bash
spark-submit task1_streaming_ingestion.py
```

### Output Location:
```
output/task1/parsed_data/
```

### Sample Output:
```csv
trip_id,driver_id,distance_km,fare_amount,timestamp
d1a2...,23,12.3,45.6,2025-04-01 17:00:12
```

---

## Task 2: Driver-Level Aggregation

### File: `task2_driver_aggregations.py`

### Objective:
- Read parsed data from Task 1
- Compute:
  - Total fare per driver
  - Average distance per driver
- Write output per batch to CSV

### Code Highlights:
- Uses `groupBy(driver_id)` to aggregate
- `withWatermark("event_time", "1 minute")` enables streaming with `update` mode
- `foreachBatch()` saves each batch to a uniquely named folder to bypass CSV sink limitations

### Steps:
```bash
spark-submit task2_driver_aggregations.py
```

### Output Location:
```
output/task2/batch_0/
output/task2/batch_1/
...
```

### Sample Output:
```csv
driver_id,total_fare,avg_distance
23,145.5,12.8
```

---

## Task 3: Windowed Time-Based Analytics

### File: `task3_windowed_analytics.py`

### Objective:
- Perform a sliding window aggregation of total fare
- Window duration: 5 minutes
- Slide interval: 1 minute

### Code Highlights:
- `window(event_time, "5 minutes", "1 minute")`: Creates overlapping windows
- `agg(sum("fare_amount"))`: Aggregates fare
- `select(window.start, window.end, ...)`: Flattens struct before writing to CSV
- `foreachBatch()`: Allows writing CSV with flattened columns

### Steps:
```bash
spark-submit task3_windowed_analytics.py
```

### Output Location:
```
output/task3/batch_0/
output/task3/batch_1/
...
```

### Sample Output:
```csv
window_start,window_end,total_fare
2025-04-01 17:00:00,2025-04-01 17:05:00,412.78
```

---

## Challenges Faced and Solutions

### 1. **CSV Sink Errors with Update/Complete Modes**
**Problem**: Spark throws `AnalysisException` when trying to write grouped streaming data directly to CSV using `update` or `complete` mode.

**Solution**: Used `foreachBatch()` to capture each batch and write it manually to a unique folder.

---

### 2. **Cannot Write Struct Columns to CSV**
**Problem**: The `window` column is a struct and cannot be written directly to CSV.

**Solution**: Flattened `window.start` and `window.end` using `select()` with `alias()`.

---

### 3. **Stream Stops After One Batch**
**Problem**: No new files = no new data = stream seems stuck

**Solution**: Ensured `data_generator.py` was running continuously and appending new rows so that Spark had data to process.

---

## Cleanup Between Runs
To avoid leftover files and checkpoints from interfering:
```bash
rm -r output/task*/
```

