import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, upper, when, current_timestamp

def main():
    # 1. Define Paths
    bronze_path = r"D:\nexus-ai\data\lakehouse\bronze\orders"
    silver_path = r"D:\nexus-ai\data\lakehouse\silver\orders"
    
    # Ensure silver directory exists
    os.makedirs(silver_path, exist_ok=True)

    # 2. Initialize Spark Session
    spark = SparkSession.builder \
        .appName("NEXUS_Silver_Ingestion") \
        .config("spark.sql.session.timeZone", "UTC") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    print(f"📂 Reading from Bronze layer: {bronze_path}")
    df_bronze = spark.read.parquet(bronze_path)

    print("🧹 Standardizing and cleaning data for Silver layer...")
    
    # 3. Apply Silver Transformations (Dedupe, Standardize, Enrich)
    df_silver = df_bronze \
        .dropDuplicates(["order_id"]) \
        .withColumn("order_timestamp", to_timestamp(col("order_date"))) \
        .withColumn("status", upper(col("status"))) \
        .withColumn("status_category", 
                    when(col("status") == "COMPLETED", "FULFILLED")
                    .when(col("status").isin("PENDING", "PROCESSING"), "IN_PROGRESS")
                    .otherwise("CANCELLED/OTHER")) \
        .withColumn("is_cancelled", when(col("status") == "CANCELLED", True).otherwise(False)) \
        .withColumn("silver_ingested_at", current_timestamp()) \
        .filter(col("order_id").isNotNull()) # Data quality: drop rows without an ID

    # Drop the raw, potentially messy date string column in favor of the typed timestamp
    df_silver = df_silver.drop("order_date")

    print(f"💾 Writing to Silver layer: {silver_path}")
    
    # 4. Write to Silver Layer
    df_silver.write \
        .mode("overwrite") \
        .parquet(silver_path)

    print("✅ Silver ingestion complete!")
    
    # Show a sample of the cleaned data
    df_silver.show(5, truncate=False)
    
    spark.stop()

if __name__ == "__main__":
    main()