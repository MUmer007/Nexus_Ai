-- 1. Suppliers
CREATE TABLE suppliers (
    supplier_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    lead_time_days INT,
    reliability_score NUMERIC(3, 2) CHECK (reliability_score >= 0.0 AND reliability_score <= 1.0)
);

-- 2. Fulfillment Centers
CREATE TABLE fulfillment_centers (
    fc_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    region VARCHAR(100),
    capacity_units INT
);

-- 3. Products
CREATE TABLE products (
    product_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    supplier_id INT REFERENCES suppliers(supplier_id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    unit_cost NUMERIC(10, 2)
);

-- 4. Customers
CREATE TABLE customers (
    customer_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    region VARCHAR(100),
    tier VARCHAR(50) DEFAULT 'standard'
);

-- 5. Orders
CREATE TABLE orders (
    order_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id) ON DELETE CASCADE,
    order_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    total_amount NUMERIC(12, 2)
);

-- 6. Order Items
CREATE TABLE order_items (
    order_item_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id INT REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id INT REFERENCES products(product_id) ON DELETE RESTRICT,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10, 2) NOT NULL
);

-- 7. Shipments (The key to our delivery-risk ML model!)
CREATE TABLE shipments (
    shipment_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id INT REFERENCES orders(order_id) ON DELETE CASCADE,
    carrier VARCHAR(100),
    shipped_at TIMESTAMPTZ,
    estimated_delivery_at TIMESTAMPTZ,
    actual_delivery_at TIMESTAMPTZ,
    status VARCHAR(50) DEFAULT 'pending'
);

-- 8. Inventory Events
CREATE TABLE inventory_events (
    event_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id INT REFERENCES products(product_id) ON DELETE RESTRICT,
    fc_id INT REFERENCES fulfillment_centers(fc_id) ON DELETE RESTRICT,
    event_type VARCHAR(50) NOT NULL, -- e.g., 'restock', 'sale', 'adjustment'
    quantity_change INT NOT NULL,
    event_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common query patterns (Phase 2 concept: performance)
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_shipments_order_id ON shipments(order_id);
CREATE INDEX idx_inventory_events_product_fc ON inventory_events(product_id, fc_id);