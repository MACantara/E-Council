from app import db, bcrypt

class Users(db.Model):
    __tablename__ = "users"

    users_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    users_first_name = db.Column(db.String(50), nullable=False)
    users_last_name = db.Column(db.String(50), nullable=False)
    users_username = db.Column(db.String(50), unique=True, nullable=False)
    users_email = db.Column(db.String(100), nullable=False)
    users_role = db.Column(db.String(50), nullable=False)
    users_password = db.Column(db.String(255), nullable=False)
    users_email_verified = db.Column(db.Integer, nullable=False)

    def set_password(self, password):
        """
        Set the user's password.

        This method will hash the given password with Bcrypt and store the hashed
        password in the users_password attribute of the object.

        Parameters:
            password (str): The user's password to be hashed and stored.

        Returns:
            None
        """
        self.users_password = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        """
        Check if the given password matches the user's stored password.

        This method will use Bcrypt to compare the given password with the hashed
        password stored in the users_password attribute of the object.

        Parameters:
            password (str): The user's password to be compared with the stored hash.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        return bcrypt.check_password_hash(self.users_password, password)

    def __repr__(self):
        """
        Return a string representation of the object.

        This string can be used to identify the object in logs, debuggers, etc.

        Returns:
            str: A string representation of the object.
        """
        return f"Users({self.users_id}, {self.users_first_name}, {self.users_last_name}, {self.users_username}, {self.users_email}, {self.users_role}, {self.users_password}, {self.users_email_verified})"