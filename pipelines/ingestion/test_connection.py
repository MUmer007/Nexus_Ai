"""Quick test: can Python talk to our Postgres database?"""

import psycopg

def main():
    # Connection string matches our docker-compose.yml
    conn_string = (
        "host=localhost "
        "port=5432 "
        "dbname=nexus_supply_chain "
        "user=nexus "
        "password=nexus123"
    )

    try:
        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                # Query the tables we just created
                cur.execute("""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY tablename;
                """)
                tables = cur.fetchall()

                print("✅ Connected to PostgreSQL successfully!")
                print(f"📊 Found {len(tables)} tables:")
                for table in tables:
                    print(f"   - {table[0]}")

    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    main()