from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class MockERP:
    """
    Simulates a university ERP system.
    In a real app, this would be an API call to a central database.
    """
    
    # Pre-registered admin and students for demo
    ADMIN_USERS = {
        "admin": pwd_context.hash("admin123")
    }

    STUDENT_DB = {
        "S001": {"name": "Alice", "password": pwd_context.hash("pass1")},
        "S002": {"name": "Bob", "password": pwd_context.hash("pass2")},
        "S003": {"name": "Charlie", "password": pwd_context.hash("pass3")},
    }

    @staticmethod
    def verify_admin(username, password):
        if username in MockERP.ADMIN_USERS:
            stored_hash = MockERP.ADMIN_USERS[username]
            return pwd_context.verify(password, stored_hash)
        return False

    @staticmethod
    def verify_student(roll_no, password):
        if roll_no in MockERP.STUDENT_DB:
            stored_hash = MockERP.STUDENT_DB[roll_no]["password"]
            if pwd_context.verify(password, stored_hash):
                return MockERP.STUDENT_DB[roll_no]
        return None
