import os
from db.db_utils import get_connection

class PaperDAO:
    """
    Data Access Object for paper-related database operations
    """
    
    @staticmethod
    def insert_paper(arxiv_id, title, md_path=None, md_content=None, pdf_path=None, published_date=None):
        """
        Insert a new paper into the database
        
        Args:
            arxiv_id: ArXiv ID of the paper
            title: Title of the paper
            md_path: Path to the markdown file
            md_content: Content of the markdown file
            pdf_path: Path to the PDF file
            published_date: Publication date of the paper (datetime object)
            
        Returns:
            The ID of the inserted paper
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = """
            INSERT INTO papers (arxiv_id, title, file_path, content, pdf_path, published_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (arxiv_id) DO UPDATE
            SET title = EXCLUDED.title,
                file_path = EXCLUDED.file_path,
                content = EXCLUDED.content,
                pdf_path = CASE 
                    WHEN EXCLUDED.pdf_path IS NOT NULL THEN EXCLUDED.pdf_path
                    ELSE papers.pdf_path
                END,
                published_date = CASE 
                    WHEN EXCLUDED.published_date IS NOT NULL THEN EXCLUDED.published_date
                    ELSE papers.published_date
                END
            RETURNING id
            """
            
            cursor.execute(query, (arxiv_id, title, md_path, md_content, pdf_path, published_date))
            paper_id = cursor.fetchone()[0]
            
            conn.commit()
            return paper_id
        except Exception as e:
            print(f"Error inserting paper: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def update_paper_pdf_path(paper_id, pdf_path):
        """
        Update the PDF path for a paper
        
        Args:
            paper_id: ID of the paper
            pdf_path: Path to the PDF file
            
        Returns:
            True if successful, False otherwise
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = """
            UPDATE papers
            SET pdf_path = %s
            WHERE id = %s
            """
            
            cursor.execute(query, (pdf_path, paper_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating paper PDF path: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def update_paper_md_path(paper_id, md_path):
        """
        Update the markdown path for a paper
        
        Args:
            paper_id: ID of the paper
            md_path: Path to the markdown file
            
        Returns:
            True if successful, False otherwise
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = """
            UPDATE papers
            SET file_path = %s
            WHERE id = %s
            """
            
            cursor.execute(query, (md_path, paper_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating paper markdown path: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def update_paper_published_date(paper_id, published_date):
        """
        Update the publication date for a paper
        
        Args:
            paper_id: ID of the paper
            published_date: Publication date (datetime object)
            
        Returns:
            True if successful, False otherwise
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = """
            UPDATE papers
            SET published_date = %s
            WHERE id = %s
            """
            
            cursor.execute(query, (published_date, paper_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating paper publication date: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_paper_by_id(paper_id):
        """
        Get a paper by its ID
        
        Args:
            paper_id: ID of the paper
            
        Returns:
            A dictionary with paper information
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT id, arxiv_id, title, file_path, pdf_path, published_date, created_at
            FROM papers
            WHERE id = %s
            """
            
            cursor.execute(query, (paper_id,))
            result = cursor.fetchone()
            
            if result:
                return {
                    "id": result[0],
                    "arxiv_id": result[1],
                    "title": result[2],
                    "md_path": result[3],
                    "pdf_path": result[4],
                    "published_date": result[5],
                    "created_at": result[6]
                }
            return None
        except Exception as e:
            print(f"Error getting paper: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_paper_by_arxiv_id(arxiv_id):
        """
        Get a paper by its ArXiv ID
        
        Args:
            arxiv_id: ArXiv ID of the paper
            
        Returns:
            A dictionary with paper information
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT id, arxiv_id, title, file_path, pdf_path, published_date, created_at
            FROM papers
            WHERE arxiv_id = %s
            """
            
            cursor.execute(query, (arxiv_id,))
            result = cursor.fetchone()
            
            if result:
                return {
                    "id": result[0],
                    "arxiv_id": result[1],
                    "title": result[2],
                    "md_path": result[3],
                    "pdf_path": result[4],
                    "published_date": result[5],
                    "created_at": result[6]
                }
            return None
        except Exception as e:
            print(f"Error getting paper: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_paper_content(paper_id):
        """
        Get the markdown content of a paper
        
        Args:
            paper_id: ID of the paper
            
        Returns:
            The markdown content or None if not found
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT content, file_path
            FROM papers
            WHERE id = %s
            """
            
            cursor.execute(query, (paper_id,))
            result = cursor.fetchone()
            
            if not result:
                return None
                
            md_content, md_path = result
            
            # If content is stored directly in the database
            if md_content:
                return md_content
                
            # Otherwise, try to read from file
            if md_path and os.path.exists(md_path):
                try:
                    with open(md_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception as file_error:
                    print(f"Error reading markdown file: {file_error}")
                    
            return None
        except Exception as e:
            print(f"Error getting paper content: {e}")
            raise
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def get_all_papers():
        """
        Get all papers
        
        Returns:
            A list of dictionaries with paper information
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT id, arxiv_id, title, file_path, pdf_path, published_date, created_at
            FROM papers
            ORDER BY created_at DESC
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            papers = []
            for result in results:
                papers.append({
                    "id": result[0],
                    "arxiv_id": result[1],
                    "title": result[2],
                    "md_path": result[3],
                    "pdf_path": result[4],
                    "published_date": result[5],
                    "created_at": result[6]
                })
            
            return papers
        except Exception as e:
            print(f"Error getting all papers: {e}")
            raise
        finally:
            if conn:
                conn.close()
                
    @staticmethod
    def delete_paper(paper_id):
        """
        Delete a paper by its ID
        
        Args:
            paper_id: ID of the paper
            
        Returns:
            True if the paper was deleted, False otherwise
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = """
            DELETE FROM papers
            WHERE id = %s
            """
            
            cursor.execute(query, (paper_id,))
            conn.commit()
            
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting paper: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()