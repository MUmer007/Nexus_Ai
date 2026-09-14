"""Benchmark: Prove that indexes actually speed up queries."""

import psycopg

def main():
    conn_string = "host=localhost port=5432 dbname=nexus_supply_chain user=nexus password=nexus123"
    
    with psycopg.connect(conn_string) as conn:
        with conn.cursor() as cur:
            # Step 1: Seed parent tables (products and fulfillment_centers)
            print("⏳ Seeding parent tables...")
            
            # Insert 100 products
            cur.execute("""
                INSERT INTO products (supplier_id, name, category, unit_cost)
                SELECT 
                    NULL,  -- supplier_id can be NULL for now
                    'Product ' || i,
                    CASE WHEN i % 3 = 0 THEN 'Electronics' 
                         WHEN i % 3 = 1 THEN 'Clothing' 
                         ELSE 'Food' END,
                    (random() * 100)::numeric(10,2)
                FROM generate_series(1, 100) AS i;
            """)
            
            # Insert 5 fulfillment centers
            cur.execute("""
                INSERT INTO fulfillment_centers (name, region, capacity_units)
                SELECT 
                    'Warehouse ' || i,
                    CASE WHEN i % 2 = 0 THEN 'East' ELSE 'West' END,
                    10000
                FROM generate_series(1, 5) AS i;
            """)
            
            conn.commit()
            print("✅ Seeded 100 products and 5 fulfillment centers.\n")

            # Step 2: Generate 50k inventory events (now referencing real IDs)
            print("⏳ Generating 50,000 dummy inventory events...")
            cur.execute("""
                INSERT INTO inventory_events (product_id, fc_id, event_type, quantity_change, event_timestamp)
                SELECT 
                    (random() * 99)::int + 1,  -- random product_id 1-100 (matches our seeded data)
                    (random() * 4)::int + 1,   -- random fc_id 1-5 (matches our seeded data)
                    CASE WHEN random() > 0.5 THEN 'sale' ELSE 'restock' END,
                    (random() * 100)::int - 50,
                    NOW() - (random() * 365 || ' days')::interval
                FROM generate_series(1, 50000);
            """)
            conn.commit()
            print("✅ Data generated.\n")

            # Step 3: Benchmark Query 1 (INDEXED)
            print("🔍 Query 1: Filtering by 'product_id' (INDEXED)")
            cur.execute("""
                EXPLAIN ANALYZE 
                SELECT * FROM inventory_events WHERE product_id = 42;
            """)
            plan_indexed = cur.fetchall()
            for row in plan_indexed:
                print(row[0])
            print("-" * 50)

            # Step 4: Benchmark Query 2 (NOT INDEXED)
            print("🔍 Query 2: Filtering by 'quantity_change' (NOT INDEXED)")
            cur.execute("""
                EXPLAIN ANALYZE 
                SELECT * FROM inventory_events WHERE quantity_change = -15;
            """)
            plan_unindexed = cur.fetchall()
            for row in plan_unindexed:
                print(row[0])
            print("-" * 50)
            
            print("\n💡 Look at the output above!")
            print("Query 1 should say 'Index Scan' or 'Bitmap Index Scan' (Fast!)")
            print("Query 2 should say 'Seq Scan' (Sequential Scan - reads every single row, Slow!)")

if __name__ == "__main__":
    main()