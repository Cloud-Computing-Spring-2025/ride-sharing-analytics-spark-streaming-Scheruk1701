from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StringType, DoubleType
from pyspark.sql.functions import to_timestamp, window, sum as _sum, col

# Create Spark session
spark = SparkSession.builder.appName("Task3-WindowedFareAggregation").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

# Define schema
schema = StructType() \
    .add("trip_id", StringType()) \
    .add("driver_id", StringType()) \
    .add("distance_km", DoubleType()) \
    .add("fare_amount", DoubleType()) \
    .add("timestamp", StringType())

# Read parsed CSV data from Task 1
df = spark.readStream \
    .option("header", "false") \
    .schema(schema) \
    .csv("output/task1/parsed_data")

# Convert timestamp and add watermark
df = df.withColumn("event_time", to_timestamp("timestamp"))

# Perform windowed aggregation
windowed_df = df \
    .withWatermark("event_time", "2 minutes") \
    .groupBy(window(col("event_time"), "5 minutes", "1 minute")) \
    .agg(_sum("fare_amount").alias("total_fare"))

# ✅ Flatten window struct for CSV writing
flattened_df = windowed_df.select(
    col("window.start").alias("window_start"),
    col("window.end").alias("window_end"),
    col("total_fare")
)

# ✅ Write to CSV using foreachBatch
def write_batch_to_csv(batch_df, batch_id):
    path = f"output/task3/batch_{batch_id}"
    batch_df.write.mode("overwrite").option("header", "true").csv(path)

# Start the streaming query
query = flattened_df.writeStream \
    .outputMode("update") \
    .foreachBatch(write_batch_to_csv) \
    .option("checkpointLocation", "output/task3/checkpoints") \
    .start()

query.awaitTermination()
