from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.local.type", "hadoop") \
    .config("spark.sql.catalog.local.warehouse", r"D:\nexus-ai\data\lakehouse\iceberg_warehouse") \
    .config("spark.jars.packages", "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0") \
    .getOrCreate()

print("📜 Iceberg Table Snapshots (Metadata):")
# Changed from .history to .snapshots to get 'committed_at' and 'operation'
spark.sql("SELECT committed_at, snapshot_id, operation FROM local.nexus.silver_orders.snapshots").show(truncate=False)

print("✅ Time Travel metadata verified!")
spark.stop()
