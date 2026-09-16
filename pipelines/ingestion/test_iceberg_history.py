from pyspark.sql import SparkSession

spark = (
    SparkSession.builder.config(
        "spark.sql.extensions",
        "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
    )
    .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.local.type", "hadoop")
    .config(
        "spark.sql.catalog.local.warehouse",
        r"D:\nexus-ai\data\lakehouse\iceberg_warehouse",
    )
    .config(
        "spark.jars.packages", "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0"
    )
    .getOrCreate()
)

print("📜 Iceberg Table History (Snapshots):")
spark.sql(
    "SELECT snapshot_id, committed_at, operation FROM local.nexus.silver_orders.history"
).show(truncate=False)

print("\n🔍 Querying the table AS OF the first snapshot:")
# Replace the snapshot_id below with the actual ID from the history output above
# spark.sql("SELECT * FROM local.nexus.silver_orders VERSION AS OF <snapshot_id>").show()

spark.stop()
