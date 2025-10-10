from db.db_utils import get_connection

class ModelDAO:
    """
    Data Access Object for model-related database operations
    """
    
    @staticmethod
    def insert_model(name, provider, context_size=None, version=None):
        """
        Insert a new model into the database
        
        Args:
            name: Name of the model
            provider: Provider of the model
            context_size: Maximum context size in tokens
            version: Version of the model
            
        Returns:
            The ID of the inserted model
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = """
            INSERT INTO models (name, provider, context_size, version)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (name, provider, version) DO UPDATE
            SET context_size = EXCLUDED.context_size
            RETURNING id
            """
            
            cursor.execute(query, (name, provider, context_size, version))
            model_id = cursor.fetchone()[0]
            
            conn.commit()
            return model_id
        except Exception as e:
            print(f"Error inserting model: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_model_by_id(model_id):
        """
        Get a model by its ID
        
        Args:
            model_id: ID of the model
            
        Returns:
            A dictionary with model information
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT id, name, provider, context_size, version, created_at
            FROM models
            WHERE id = %s
            """
            
            cursor.execute(query, (model_id,))
            result = cursor.fetchone()
            
            if result:
                return {
                    "id": result[0],
                    "name": result[1],
                    "provider": result[2],
                    "context_size": result[3],
                    "version": result[4],
                    "created_at": result[5]
                }
            return None
        except Exception as e:
            print(f"Error getting model: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_model_by_name_provider(name, provider, version=None):
        """
        Get a model by its name and provider
        
        Args:
            name: Name of the model
            provider: Provider of the model
            version: Version of the model (optional)
            
        Returns:
            A dictionary with model information
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            if version:
                query = """
                SELECT id, name, provider, context_size, version, created_at
                FROM models
                WHERE name = %s AND provider = %s AND version = %s
                """
                cursor.execute(query, (name, provider, version))
            else:
                query = """
                SELECT id, name, provider, context_size, version, created_at
                FROM models
                WHERE name = %s AND provider = %s
                ORDER BY created_at DESC
                LIMIT 1
                """
                cursor.execute(query, (name, provider))
            
            result = cursor.fetchone()
            
            if result:
                return {
                    "id": result[0],
                    "name": result[1],
                    "provider": result[2],
                    "context_size": result[3],
                    "version": result[4],
                    "created_at": result[5]
                }
            return None
        except Exception as e:
            print(f"Error getting model: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_all_models():
        """
        Get all models
        
        Returns:
            A list of dictionaries with model information
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT id, name, provider, context_size, version, created_at
            FROM models
            ORDER BY provider, name
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            models = []
            for result in results:
                models.append({
                    "id": result[0],
                    "name": result[1],
                    "provider": result[2],
                    "context_size": result[3],
                    "version": result[4],
                    "created_at": result[5]
                })
            
            return models
        except Exception as e:
            print(f"Error getting all models: {e}")
            raise
        finally:
            if conn:
                conn.close() 