from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, upper
from pyspark.sql.types import IntegerType, LongType, StringType, StructField, StructType


def main():
    spark = (
        SparkSession.builder.appName("NEXUS_Silver_Streaming_Ingestion")
        .config("spark.sql.session.timeZone", "UTC")
        .config(
            "spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3,org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0",
        )
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")
    print("📡 Connecting to Kafka topic: nexus.public.orders...")

    # 1. Define the INNER payload schema (matching Debezium's 'rewrite' mode)
    payload_schema = StructType(
        [
            StructField("order_id", IntegerType(), True),
            StructField("customer_id", IntegerType(), True),
            StructField("order_date", LongType(), True),
            StructField("status", StringType(), True),
            StructField("total_amount", StringType(), True),
            StructField(
                "__deleted", StringType(), True
            ),  # 'true' or 'false' (replaces __op)
        ]
    )

    # 2. Define the OUTER envelope schema
    envelope_schema = StructType([StructField("payload", payload_schema, True)])

    # 3. Read from Kafka
    kafka_df = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", "localhost:9092")
        .option("subscribe", "nexus.public.orders")
        .option("startingOffsets", "latest")
        .load()
    )

    # 4. Parse the Envelope
    parsed_df = kafka_df.select(
        from_json(col("value").cast("string"), envelope_schema).alias("envelope")
    )

    # 5. Extract, Transform, and Filter
    silver_df = parsed_df.select(
        col("envelope.payload.order_id"),
        col("envelope.payload.customer_id"),
        # Convert Microseconds to Seconds, then cast to Timestamp
        (col("envelope.payload.order_date") / 1000000.0)
        .cast("timestamp")
        .alias("order_timestamp"),
        upper(col("envelope.payload.status")).alias("status"),
        col("envelope.payload.total_amount").alias("raw_amount_b64"),
        col("envelope.payload.__deleted").alias("is_deleted"),
    ).filter(
        # Filter out nulls and soft-deletes
        (col("order_id").isNotNull()) & (col("is_deleted") != "true")
    )

    # 6. Write to Console
    query = (
        silver_df.writeStream.outputMode("append")
        .format("console")
        .option("truncate", "false")
        .trigger(processingTime="5 seconds")
        .start()
    )

    print("✅ Streaming query started! Go to your OTHER terminal and insert a new row.")
    query.awaitTermination()


if __name__ == "__main__":
    main()
