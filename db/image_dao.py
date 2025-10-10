"""
Data Access Object for paper images.
"""

import os
from db.db_utils import get_connection
from psycopg2.extras import RealDictCursor
import base64

def insert_paper_image(paper_id, page_number, image_id, image_path, caption=None, position=None):
    """
    Insert a paper image into the database.
    
    Args:
        paper_id: ID of the paper
        page_number: Page number where the image appears
        image_id: Unique identifier for the image
        image_path: Path to the saved image file
        caption: Optional image caption
        position: Optional dictionary with x, y, width, height
        
    Returns:
        ID of the inserted image or None on failure
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # Default position values
            x, y, width, height = 0, 0, 0, 0
            
            # Extract position if provided
            if position:
                x = position.get('x', 0)
                y = position.get('y', 0)
                width = position.get('width', 0)
                height = position.get('height', 0)
            
            cursor.execute("""
            INSERT INTO paper_images 
                (paper_id, page_number, image_id, image_path, caption, x, y, width, height)
            VALUES 
                (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """, (paper_id, page_number, image_id, image_path, caption, x, y, width, height))
            
            result = cursor.fetchone()
            conn.commit()
            return result[0] if result else None
            
    except Exception as e:
        print(f"Error inserting paper image: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

def get_paper_images(paper_id):
    """
    Get all images for a paper.
    
    Args:
        paper_id: ID of the paper
        
    Returns:
        List of image dictionaries
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
            SELECT * FROM paper_images
            WHERE paper_id = %s
            ORDER BY page_number, id
            """, (paper_id,))
            
            return cursor.fetchall()
            
    except Exception as e:
        print(f"Error getting paper images: {e}")
        return []
    finally:
        if conn:
            conn.close()

def save_image_from_base64(base64_data, output_path):
    """
    Saves an image from base64 data to a file
    
    Args:
        base64_data: Base64 encoded image data
        output_path: Path to save the image to
        
    Returns:
        Boolean indicating success
    """
    try:
        # If the base64 data has a prefix like 'data:image/jpeg;base64,', remove it
        if ';base64,' in base64_data:
            base64_data = base64_data.split(';base64,')[1]
        
        # Decode the base64 data and save to file
        image_data = base64.b64decode(base64_data)
        with open(output_path, 'wb') as f:
            f.write(image_data)
        print(f"- Saved image to {output_path}")
        return True
    except Exception as e:
        print(f"Error saving image: {type(e).__name__}: {str(e)}")
        return False

def delete_paper_images(paper_id):
    """
    Delete all images for a paper.
    
    Args:
        paper_id: ID of the paper
        
    Returns:
        Number of deleted images
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
            DELETE FROM paper_images
            WHERE paper_id = %s
            RETURNING id
            """, (paper_id,))
            
            results = cursor.fetchall()
            conn.commit()
            return len(results)
            
    except Exception as e:
        print(f"Error deleting paper images: {e}")
        if conn:
            conn.rollback()
        return 0
    finally:
        if conn:
            conn.close() 