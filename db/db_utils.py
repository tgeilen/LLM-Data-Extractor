import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "ocr_analysis")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")

def get_connection():
    """
    Create a connection to the PostgreSQL database
    
    Returns:
        A connection object to the database
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Error connecting to PostgreSQL database: {e}")
        raise

def create_schema():
    """
    Create the database schema if it doesn't exist
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Enable array extension if needed
        cursor.execute("CREATE EXTENSION IF NOT EXISTS intarray;")
        
        # Create papers table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id SERIAL PRIMARY KEY,
            arxiv_id VARCHAR(50) UNIQUE,
            title TEXT NOT NULL,
            file_path TEXT,
            pdf_path TEXT,
            content TEXT,
            published_date TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create models table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS models (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            provider VARCHAR(100) NOT NULL,
            context_size INTEGER,
            version VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name, provider, version)
        )
        """)
        
        # Create extraction_runs table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS extraction_runs (
            id SERIAL PRIMARY KEY,
            paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
            model_id INTEGER NOT NULL REFERENCES models(id) ON DELETE CASCADE,
            run_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            temperature REAL,
            raw_response TEXT,
            UNIQUE(paper_id, model_id, run_date)
        )
        """)
        
        # Create extracted_fields table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS extracted_fields (
            id SERIAL PRIMARY KEY,
            run_id INTEGER NOT NULL REFERENCES extraction_runs(id) ON DELETE CASCADE,
            field_name VARCHAR(100) NOT NULL,
            value TEXT,
            confidence REAL NOT NULL,
            references_text TEXT,
            model_instance_id INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(run_id, field_name, model_instance_id)
        )
        """)
        
        # Create paper_images table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS paper_images (
            id SERIAL PRIMARY KEY,
            paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
            page_number INTEGER,
            image_id TEXT,
            image_path TEXT NOT NULL,
            caption TEXT,
            x FLOAT,
            y FLOAT,
            width FLOAT,
            height FLOAT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        print("Database schema created successfully")
        
    except Exception as e:
        print(f"Error creating schema: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def drop_schema():
    """
    Drop all tables - use with caution!
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        DROP TABLE IF EXISTS paper_images CASCADE;
        DROP TABLE IF EXISTS extracted_fields CASCADE;
        DROP TABLE IF EXISTS extraction_runs CASCADE;
        DROP TABLE IF EXISTS models CASCADE;
        DROP TABLE IF EXISTS papers CASCADE;
        """)
        
        conn.commit()
        print("Database schema dropped successfully")
    except Exception as e:
        print(f"Error dropping database schema: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # If this file is run directly, create the schema
    create_schema() 