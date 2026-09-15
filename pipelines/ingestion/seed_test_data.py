"""Insert test data into PostgreSQL for pipeline testing."""

import psycopg

def main():
    conn_string = "host=localhost port=5432 dbname=nexus_supply_chain user=nexus password=nexus123"
    
    with psycopg.connect(conn_string) as conn:
        with conn.cursor() as cur:
            # Insert customers
            print("👥 Inserting customers...")
            cur.execute("""
                INSERT INTO customers (name, region, tier) VALUES 
                ('Alice Johnson', 'North', 'premium'),
                ('Bob Smith', 'South', 'standard');
            """)
            
            # Insert orders
            print("📦 Inserting orders...")
            cur.execute("""
                INSERT INTO orders (customer_id, status, total_amount) VALUES 
                (1, 'completed', 150.00),
                (1, 'pending', 75.50),
                (2, 'completed', 200.00),
                (2, 'cancelled', 50.00);
            """)
            
            conn.commit()
            print("✅ Test data inserted successfully!")

if __name__ == "__main__":
    main()