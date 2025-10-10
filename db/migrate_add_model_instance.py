#!/usr/bin/env python3
"""
Migration script to add model_instance_id column to extracted_fields table.
"""

import os
import sys
from dotenv import load_dotenv
from db.db_utils import get_connection

def migrate_add_model_instance_id():
    """
    Add model_instance_id column to extracted_fields table and update constraints.
    This is a non-destructive migration that maintains all existing data.
    """
    conn = None
    try:
        # Connect to the database
        print("Connecting to database...")
        conn = get_connection()
        cursor = conn.cursor()
        
        # Start a transaction
        cursor.execute("BEGIN;")
        
        # Check if the column already exists
        cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'extracted_fields' AND column_name = 'model_instance_id';
        """)
        
        column_exists = cursor.fetchone() is not None
        
        if column_exists:
            print("Column model_instance_id already exists, skipping migration.")
            conn.rollback()
            return True
        
        print("Adding model_instance_id column to extracted_fields table...")
        
        # Step 1: Add the new column with default value 0
        cursor.execute("""
        ALTER TABLE extracted_fields
        ADD COLUMN model_instance_id INTEGER DEFAULT 0;
        """)
        
        # Step 2: Update all existing records to have model_instance_id = 0
        cursor.execute("""
        UPDATE extracted_fields
        SET model_instance_id = 0;
        """)
        
        # Step 3: Drop the existing unique constraint
        cursor.execute("""
        ALTER TABLE extracted_fields
        DROP CONSTRAINT IF EXISTS extracted_fields_run_id_field_name_key;
        """)
        
        # Step 4: Add the new unique constraint including model_instance_id
        cursor.execute("""
        ALTER TABLE extracted_fields
        ADD CONSTRAINT extracted_fields_run_id_field_name_model_instance_id_key
        UNIQUE (run_id, field_name, model_instance_id);
        """)
        
        # Commit the transaction
        cursor.execute("COMMIT;")
        
        print("Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during migration: {e}")
        if conn:
            print("Rolling back changes...")
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    print("Starting migration to add model_instance_id column...")
    
    # Run the migration
    success = migrate_add_model_instance_id()
    
    # Exit with appropriate status code
    if success:
        print("Migration completed successfully.")
        sys.exit(0)
    else:
        print("Migration failed.")
        sys.exit(1) 