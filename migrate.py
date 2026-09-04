import sqlite3

DB_NAME = "merchantos.db"

connection = sqlite3.connect(DB_NAME)

cursor = connection.cursor()


# ------------------------------------------------
# Check existing columns
# ------------------------------------------------

cursor.execute("PRAGMA table_info(orders)")

columns = [row[1] for row in cursor.fetchall()]

print("Existing orders columns:")
print(columns)


# ------------------------------------------------
# Add payment_status
# ------------------------------------------------

if "payment_status" not in columns:

    cursor.execute("""
        ALTER TABLE orders
        ADD COLUMN payment_status TEXT DEFAULT 'NOT_STARTED'
    """)

    print("Added payment_status column.")

else:

    print("payment_status already exists.")


# ------------------------------------------------
# Add payment_attempts
# ------------------------------------------------

if "payment_attempts" not in columns:

    cursor.execute("""
        ALTER TABLE orders
        ADD COLUMN payment_attempts INTEGER DEFAULT 0
    """)

    print("Added payment_attempts column.")

else:

    print("payment_attempts already exists.")


# ------------------------------------------------
# Add payment_id
# ------------------------------------------------

if "payment_id" not in columns:

    cursor.execute("""
        ALTER TABLE orders
        ADD COLUMN payment_id TEXT
    """)

    print("Added payment_id column.")

else:

    print("payment_id already exists.")

if "razorpay_order_id" not in columns:
    cursor.execute("""
        ALTER TABLE orders
        ADD COLUMN razorpay_order_id TEXT
    """)
    print("Added razorpay_order_id column.")
else:
    print("razorpay_order_id already exists.")


# ------------------------------------------------
# Save changes
# ------------------------------------------------

connection.commit()

connection.close()

print("Database migration completed successfully.")