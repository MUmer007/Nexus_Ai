import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, upper, when, current_timestamp

def main():
    # 1. Define Paths
    bronze_path = r"D:\nexus-ai\data\lakehouse\bronze\orders"
    # Iceberg warehouse directory
    iceberg_warehouse = r"D:\nexus-ai\data\lakehouse\iceberg_warehouse"
    os.makedirs(iceberg_warehouse, exist_ok=True)

    # 2. Initialize Spark Session with Iceberg Extensions
    # CRITICAL FIX: PySpark 3.5.x pip wheels are built with Scala 2.12. 
    # We MUST use the _2.12 Iceberg runtime to match.
    spark = SparkSession.builder \
        .appName("NEXUS_Silver_Iceberg_Ingestion") \
        .config("spark.sql.session.timeZone", "UTC") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.local.type", "hadoop") \
        .config("spark.sql.catalog.local.warehouse", iceberg_warehouse) \
        .config("spark.jars.packages", "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    print(f"📂 Reading from Bronze layer: {bronze_path}")
    df_bronze = spark.read.parquet(bronze_path)

    print("🧹 Standardizing and cleaning data for Silver Iceberg table...")
    
    # 3. Apply Silver Transformations
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
        .filter(col("order_id").isNotNull()) \
        .drop("order_date")

    # 4. Write to Iceberg Table
    print("💾 Writing to Iceberg table: local.nexus.silver_orders")
    
    df_silver.writeTo("local.nexus.silver_orders") \
        .tableProperty("format-version", "2") \
        .createOrReplace()

    print("✅ Silver Iceberg ingestion complete!")
    
    # 5. Verify by reading back from Iceberg
    print("\n🔍 Verifying Iceberg table contents:")
    spark.read.table("local.nexus.silver_orders").show(5, truncate=False)
    
    spark.stop()

if __name__ == "__main__":
    main()