"""Bronze Layer: Ingest raw data from PostgreSQL into the lakehouse."""

import os

from pyspark.sql import SparkSession


def main():
    # Define paths
    base_path = os.path.abspath("data/lakehouse")
    bronze_path = os.path.join(base_path, "bronze", "orders")

    print(f"📂 Bronze output path: {bronze_path}")

    # Initialize Spark with PostgreSQL JDBC driver
    spark = (
        SparkSession.builder.appName("NEXUS Bronze Ingestion")
        .config("spark.jars.packages", "org.postgresql:postgresql:42.7.2")
        .getOrCreate()
    )

    try:
        # Read from PostgreSQL
        print("🔌 Connecting to PostgreSQL...")
        df = (
            spark.read.format("jdbc")
            .option("url", "jdbc:postgresql://localhost:5432/nexus_supply_chain")
            .option("dbtable", "orders")
            .option("user", "nexus")
            .option("password", "nexus123")
            .option("driver", "org.postgresql.Driver")
            .load()
        )

        print(f"✅ Loaded {df.count()} rows from orders table")
        df.show(5)

        # Write to Bronze layer as Parquet (append mode)
        print(f"💾 Writing to Bronze layer: {bronze_path}")
        df.write.mode("overwrite").parquet(bronze_path)

        print("✅ Bronze ingestion complete!")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
