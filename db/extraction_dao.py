import json
from db.db_utils import get_connection

class ExtractionDAO:
    """
    Data Access Object for extraction-related database operations
    """
    
    @staticmethod
    def insert_extraction_run(paper_id, model_id, temperature=None, raw_response=None):
        """
        Insert a new extraction run into the database
        
        Args:
            paper_id: ID of the paper
            model_id: ID of the model
            temperature: Temperature used for generation
            raw_response: Raw response from the model (as dict or JSON string)
            
        Returns:
            The ID of the inserted extraction run
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Convert raw_response to JSON string if it's a dict
            if isinstance(raw_response, dict):
                raw_response = json.dumps(raw_response)
            
            query = """
            INSERT INTO extraction_runs (paper_id, model_id, temperature, raw_response)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """
            
            cursor.execute(query, (paper_id, model_id, temperature, raw_response))
            run_id = cursor.fetchone()[0]
            
            conn.commit()
            return run_id
        except Exception as e:
            print(f"Error inserting extraction run: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_extraction_run(run_id):
        """
        Get an extraction run by its ID
        
        Args:
            run_id: ID of the extraction run
            
        Returns:
            A dictionary with extraction run information
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT id, paper_id, model_id, run_date, temperature
            FROM extraction_runs
            WHERE id = %s
            """
            
            cursor.execute(query, (run_id,))
            result = cursor.fetchone()
            
            if result:
                return {
                    "id": result[0],
                    "paper_id": result[1],
                    "model_id": result[2],
                    "run_date": result[3],
                    "temperature": result[4]
                }
            return None
        except Exception as e:
            print(f"Error getting extraction run: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_raw_response(run_id):
        """
        Get the raw response for an extraction run
        
        Args:
            run_id: ID of the extraction run
            
        Returns:
            The raw response as a dictionary
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT raw_response
            FROM extraction_runs
            WHERE id = %s
            """
            
            cursor.execute(query, (run_id,))
            result = cursor.fetchone()
            
            if result and result[0]:
                return result[0]
            return None
        except Exception as e:
            print(f"Error getting raw response: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_extraction_runs_for_paper(paper_id):
        """
        Get all extraction runs for a paper
        
        Args:
            paper_id: ID of the paper
            
        Returns:
            A list of dictionaries with extraction run information
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT er.id, er.paper_id, er.model_id, er.run_date, er.temperature, 
                   m.name, m.provider
            FROM extraction_runs er
            JOIN models m ON er.model_id = m.id
            WHERE er.paper_id = %s
            ORDER BY er.run_date DESC
            """
            
            cursor.execute(query, (paper_id,))
            results = cursor.fetchall()
            
            runs = []
            for result in results:
                runs.append({
                    "id": result[0],
                    "paper_id": result[1],
                    "model_id": result[2],
                    "run_date": result[3],
                    "temperature": result[4],
                    "model_name": result[5],
                    "model_provider": result[6]
                })
            
            return runs
        except Exception as e:
            print(f"Error getting extraction runs: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def insert_extracted_field(run_id, field_name, value, confidence, references_text=None, model_instance_id=0):
        """
        Insert a new extracted field into the database
        
        Args:
            run_id: ID of the extraction run
            field_name: Name of the field
            value: Value of the field
            confidence: Confidence score (0-100)
            references_text: References text
            model_instance_id: Identifier for which model in the paper this field belongs to
            
        Returns:
            The ID of the inserted field
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = """
            INSERT INTO extracted_fields (run_id, field_name, value, confidence, references_text, model_instance_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (run_id, field_name, model_instance_id) DO UPDATE
            SET value = EXCLUDED.value,
                confidence = EXCLUDED.confidence,
                references_text = EXCLUDED.references_text
            RETURNING id
            """
            
            cursor.execute(query, (run_id, field_name, value, confidence, references_text, model_instance_id))
            field_id = cursor.fetchone()[0]
            
            conn.commit()
            return field_id
        except Exception as e:
            print(f"Error inserting extracted field: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_extracted_fields(run_id):
        """
        Get all extracted fields for a run
        
        Args:
            run_id: ID of the extraction run
            
        Returns:
            A list of dictionaries with extracted field information
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT id, field_name, value, confidence, references_text, model_instance_id
            FROM extracted_fields
            WHERE run_id = %s
            ORDER BY model_instance_id, field_name
            """
            
            cursor.execute(query, (run_id,))
            results = cursor.fetchall()
            
            fields = []
            for result in results:
                fields.append({
                    "id": result[0],
                    "field_name": result[1],
                    "value": result[2],
                    "confidence": result[3],
                    "references_text": result[4],
                    "model_instance_id": result[5]
                })
            
            return fields
        except Exception as e:
            print(f"Error getting extracted fields: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_field_values_across_runs(paper_id, field_name, model_instance_id=0):
        """
        Get values for a specific field across all runs for a paper
        
        Args:
            paper_id: ID of the paper
            field_name: Name of the field to get values for
            model_instance_id: Identifier for which model in the paper this field belongs to
            
        Returns:
            A list of dictionaries with field values and run information
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT ef.value, ef.confidence, ef.references_text, 
                   er.id as run_id, er.temperature, m.name as model_name, m.provider
            FROM extracted_fields ef
            JOIN extraction_runs er ON ef.run_id = er.id
            JOIN models m ON er.model_id = m.id
            WHERE er.paper_id = %s AND ef.field_name = %s AND ef.model_instance_id = %s
            ORDER BY er.run_date
            """
            
            cursor.execute(query, (paper_id, field_name, model_instance_id))
            results = cursor.fetchall()
            
            values = []
            for result in results:
                values.append({
                    "value": result[0],
                    "confidence": result[1],
                    "references_text": result[2],
                    "run_id": result[3],
                    "temperature": result[4],
                    "model_name": result[5],
                    "model_provider": result[6]
                })
            
            return values
        except Exception as e:
            print(f"Error getting field values: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def store_extraction_results(run_id, extraction_data):
        """
        Store extraction results in the database
        
        Args:
            run_id: ID of the extraction run
            extraction_data: Dictionary or list of dictionaries with extraction results
            
        Returns:
            List of field IDs created
        """
        field_ids = []
        
        # Handle case where extraction_data is a list of models
        if isinstance(extraction_data, list):
            # Process each model in the list with a different model_instance_id
            for model_idx, model_data in enumerate(extraction_data):
                if not isinstance(model_data, dict):
                    print(f"Warning: Expected dict for model data, got {type(model_data)}")
                    continue
                    
                # Store each field with the corresponding model_instance_id
                for field_name, field_data in model_data.items():
                    if isinstance(field_data, dict):
                        value = field_data.get('value')
                        confidence = field_data.get('confidence', 0)
                        references = field_data.get('references_text')
                        
                        if value is not None:
                            field_id = ExtractionDAO.insert_extracted_field(
                                run_id, field_name, value, confidence, references, model_idx
                            )
                            field_ids.append(field_id)
                    else:
                        # If just a simple value, use default confidence
                        value = field_data
                        if value is not None:
                            field_id = ExtractionDAO.insert_extracted_field(
                                run_id, field_name, value, 50, None, model_idx
                            )
                            field_ids.append(field_id)
        
        # Handle case where extraction_data is a single model (dict)
        elif isinstance(extraction_data, dict):
            # Store with model_instance_id = 0 (default)
            for field_name, field_data in extraction_data.items():
                if isinstance(field_data, dict):
                    value = field_data.get('value')
                    confidence = field_data.get('confidence', 0)
                    references = field_data.get('references_text')
                    
                    if value is not None:
                        field_id = ExtractionDAO.insert_extracted_field(
                            run_id, field_name, value, confidence, references
                        )
                        field_ids.append(field_id)
                else:
                    # If just a simple value, use default confidence
                    value = field_data
                    if value is not None:
                        field_id = ExtractionDAO.insert_extracted_field(
                            run_id, field_name, value, 50, None
                        )
                        field_ids.append(field_id)
        
        return field_ids 