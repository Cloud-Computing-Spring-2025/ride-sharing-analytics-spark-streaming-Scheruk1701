from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StringType, DoubleType
from pyspark.sql.functions import sum as _sum, avg, to_timestamp

# Create Spark session
spark = SparkSession.builder.appName("Task2-DriverAggregations").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

# Schema (same as Task 1)
schema = StructType() \
    .add("trip_id", StringType()) \
    .add("driver_id", StringType()) \
    .add("distance_km", DoubleType()) \
    .add("fare_amount", DoubleType()) \
    .add("timestamp", StringType())

# Read streaming data from CSV output of Task 1
df = spark.readStream \
    .option("header", "false") \
    .schema(schema) \
    .csv("output/task1/parsed_data")

# Convert timestamp to TimestampType
df = df.withColumn("event_time", to_timestamp("timestamp"))

# Aggregation with watermark
agg_df = df.withWatermark("event_time", "1 minute") \
    .groupBy("driver_id") \
    .agg(
        _sum("fare_amount").alias("total_fare"),
        avg("distance_km").alias("avg_distance")
    )

# ✅ Define custom function to handle each batch
def save_to_csv(batch_df, batch_id):
    output_path = f"output/task2/batch_{batch_id}"
    batch_df.write.mode("overwrite").option("header", "true").csv(output_path)

# ✅ Use foreachBatch to save each batch's output
query = agg_df.writeStream \
    .outputMode("update") \
    .foreachBatch(save_to_csv) \
    .option("checkpointLocation", "output/task2/checkpoints") \
    .start()

query.awaitTermination()
