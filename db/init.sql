-- Demo e-commerce database ("shop") with sample data.

CREATE TABLE customers (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT UNIQUE NOT NULL,
    city        TEXT NOT NULL,
    signup_date DATE NOT NULL
);

CREATE TABLE products (
    id       SERIAL PRIMARY KEY,
    name     TEXT NOT NULL,
    category TEXT NOT NULL,
    price    NUMERIC(10,2) NOT NULL
);

CREATE TABLE orders (
    id          SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(id),
    order_date  DATE NOT NULL,
    status      TEXT NOT NULL CHECK (status IN ('completed', 'pending', 'cancelled'))
);

CREATE TABLE order_items (
    id         SERIAL PRIMARY KEY,
    order_id   INT NOT NULL REFERENCES orders(id),
    product_id INT NOT NULL REFERENCES products(id),
    quantity   INT NOT NULL,
    unit_price NUMERIC(10,2) NOT NULL
);

INSERT INTO customers (name, email, city, signup_date)
SELECT 'Customer ' || g,
       'customer' || g || '@example.com',
       (ARRAY['Delhi','Mumbai','Bengaluru','Chennai','Kolkata','Pune','Hyderabad'])[1 + (g % 7)],
       DATE '2024-01-01' + (g * 3 % 600)
FROM generate_series(1, 200) g;

INSERT INTO products (name, category, price)
SELECT 'Product ' || g,
       (ARRAY['Electronics','Clothing','Books','Home','Sports'])[1 + (g % 5)],
       (199 + (g * 137 % 4800))::numeric(10,2)
FROM generate_series(1, 30) g;

INSERT INTO orders (customer_id, order_date, status)
SELECT 1 + (g * 7 % 200),
       DATE '2025-01-01' + (g * 11 % 640),
       (ARRAY['completed','completed','completed','pending','cancelled'])[1 + (g % 5)]
FROM generate_series(1, 1500) g;

INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT 1 + (g % 1500), p.id, 1 + (g % 4), p.price
FROM generate_series(1, 4000) g
JOIN products p ON p.id = 1 + (g * 13 % 30);

-- Layer 3 of safety: a database user that can only SELECT.
CREATE ROLE nl2sql_reader LOGIN PASSWORD 'reader_pass';
GRANT CONNECT ON DATABASE shop TO nl2sql_reader;
GRANT USAGE ON SCHEMA public TO nl2sql_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO nl2sql_reader;
