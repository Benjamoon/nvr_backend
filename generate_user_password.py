from werkzeug.security import generate_password_hash
import getpass

password = getpass.getpass("Enter the password:")

print("Result: ", generate_password_hash(password))