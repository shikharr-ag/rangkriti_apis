
import random
import string
from firebase_admin import firestore

def generate_alphanumeric_password(length=12, include_symbols=False):
    """Generates a random alphanumeric password.

    Args:
        length: The desired length of the password (default: 12).
        include_symbols: Whether to include symbols in the password (default: False).

    Returns:
        A randomly generated alphanumeric password as a string.
    """

    characters = string.ascii_letters + string.digits  # Alphanumeric characters

    if include_symbols:
        characters += string.punctuation  # Add symbols

    if length <= 0:
      raise ValueError("Password length must be greater than zero.")

    password = ''.join(random.choice(characters) for i in range(length))
    return password

def get_document(collection_name, document_id,db):
    """Retrieves a document from Firestore.

    Args:
        collection_name: The name of the Firestore collection.
        document_id: The ID of the document to retrieve.

    Returns:
        A dictionary containing the document data, or None if the document doesn't exist or an error occurs.
    """
    try:
        doc_ref = db.collection(collection_name).document(document_id)  # Create a document reference
        doc = doc_ref.get()  # Get the document

        if doc.exists:
            doc_data = doc.to_dict()  # Convert the document to a dictionary
            print(f"Document data: {doc_data}")
            return doc_data
        else:
            print(f"No such document! in {collection_name} with ID: {document_id}")
            return None

    except Exception as e:
        print(f"Error retrieving document: {e}")
        return None

def create_verified_user(email,auth,db):
    """Creates a verified user in Firebase Auth and Firestore, or retrieves existing user info.

    Args:
        email: The email address of the user.

    Returns:
        A dictionary containing the user's UID and password, or None if an error occurs.
    """
    try:
        try:  # Nested try for get_user_by_email to handle auth errors separately
            registered_user = auth.get_user_by_email(email)
        except auth.UserNotFoundError: # Handle UserNotFoundError specifically
            registered_user = None # Set to None if user not found
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None # Return None if any other error occurs

        if registered_user:
            uid = registered_user.uid
            user_auth_info = get_document('user_auth', uid,db=db)

            if user_auth_info:
                user_pass = user_auth_info.get('password')  # Use .get() to avoid KeyError
                return {"uid": uid, "password": user_pass}
            else:
                print(f"Warning: User auth info not found in Firestore for UID: {uid}") # Log the warning.
                return None  # Or consider re-creating the user_auth document if needed.
        else:
            password = generate_alphanumeric_password()  # Generate password first
            try:  # Nested try for user creation to handle auth errors separately
                user = auth.create_user(
                    email=email,
                    email_verified=True,
                    password=password,
                    display_name=email.split("@")[0],
                    disabled=False
                )
            except Exception as e:
                print(f"Error creating user: {e}")
                return None # Return None if any error occurs

            try: # Nested try for Firestore write to handle firestore errors separately
                db.collection('user_auth').document(user.uid).set({
                    "password": password,
                    "email": email,
                    "verified": True,
                    "createdAt": firestore.SERVER_TIMESTAMP,
                })
                print(f'Successfully created new user: {user.uid}')
                return {"uid": user.uid, "password": password}
            except Exception as e:
                print(f"Error writing to Firestore: {e}")
                try: # Delete user if Firestore write fails
                    auth.delete_user(user.uid)
                    print(f"Deleted user {user.uid} due to Firestore error.")
                except Exception as e:
                    print(f"Error deleting user {user.uid}: {e}")
                return None # Return None if any error occurs

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None