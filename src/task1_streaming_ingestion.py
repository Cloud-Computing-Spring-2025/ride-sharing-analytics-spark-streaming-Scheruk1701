from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType, DoubleType

# Create Spark session
spark = SparkSession.builder.appName("RideSharingStream").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

# Read from socket
raw_stream = spark.readStream.format("socket") \
    .option("host", "localhost") \
    .option("port", 9999) \
    .load()

# Define schema
schema = StructType() \
    .add("trip_id", StringType()) \
    .add("driver_id", StringType()) \
    .add("distance_km", DoubleType()) \
    .add("fare_amount", DoubleType()) \
    .add("timestamp", StringType())

# Parse JSON into columns
parsed_df = raw_stream.select(from_json(col("value"), schema).alias("data")).select("data.*")

# Write to CSV in output folder
query = parsed_df.writeStream \
    .outputMode("append") \
    .format("csv") \
    .option("path", "output/task1/parsed_data") \
    .option("checkpointLocation", "output/task1/checkpoints/parsed_data") \
    .start()

query.awaitTermination()
