
import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore,auth
import random
from send_otp import send_email, generate_otp
from dotenv import load_dotenv
from admin import create_verified_user
app = Flask(__name__)
load_dotenv()

cred = credentials.Certificate('serviceAcountKey.json')
print(f"Project ID: {os.getenv('FIREBASE_PROJECT_ID')}")
print(f"Private Key (first 20 chars): {os.getenv('FIREBASE_PRIVATE_KEY')[:20]}...")
firebase_admin.initialize_app(cred)

db = firestore.client()  # Get Firestore client

def generate_otp(length=6):
    return "".join([str(random.randint(0, 9)) for _ in range(length)])

def create_otp_email_html(otp):  # Your HTML email template
    html = """<!DOCTYPE html>...""".format(otp)  # ... (your HTML)
    return html

def delete_documents(collection_name, field, operator, value):
    """Deletes documents in a Firestore collection based on a query."""

    try:
        collection_ref = db.collection(collection_name)
        query = collection_ref.where(field_path=field, filter=operator, value=value) # Create query
        docs = query.stream() # Get documents that match the query
        
        batch = db.batch() # Create a batch write for efficiency

        deleted_count = 0
        for doc in docs:
            batch.delete(doc.reference) # Add each document deletion to the batch
            deleted_count +=1

        if deleted_count > 0:
            batch.commit() # Commit the batch delete operation.
            print(f"{deleted_count} documents deleted successfully from {collection_name}.")
        else:
            print(f"No documents found in {collection_name} matching the criteria.")

    except Exception as e:
        print(f"Error deleting documents: {e}")

def get_otp_document(email):
    """Retrieves an OTP document from Firestore based on email."""

    try:
        otps_ref = db.collection('otps')
        query = otps_ref.where("email", "==", email).limit(1)  # Limit to 1 document
        docs = query.stream()

        for doc in docs:  # Iterate through the (at most one) document
            otp_data = doc.to_dict()  # Convert the document to a dictionary
            print(f"OTP Document Data: {otp_data}")
            return otp_data # Return the data
            # You can access individual fields like this:
            # otp_code = otp_data.get('otp')
            # expiry_time = otp_data.get('expiry')
            # ... and so on

        # If no document is found:
        print(f"No OTP document found for email: {email}")
        return None  # Or return an empty dictionary {} if you prefer

    except Exception as e:
        print(f"Error retrieving OTP document: {e}")
        return None  # Or raise the exception if you want to handle it differently

@app.route('/api/auth', methods=['POST'])
def authenticate_user():
    try:
        data=request.get_json()
        email = data.get("email")
        print(f"Received JSON: {data}")
        otp = generate_otp()
        print(f"Otp is: {otp}")
        # pprint("otp is ",otp)
        # 1. Store OTP in Firestore (with an expiry time):
        delete_documents('otps','email','==',email)
        print(f"deleted previous otps for {email} ")
        otp_ref = db.collection('otps').document()
        # # Get current time in milliseconds and add 10 minutes
        expiry_time = int((datetime.datetime.now() + timedelta(minutes=10)).timestamp() * 1000)

        print(f"expiry at {expiry_time} ")
        otp_ref.set({
            'otp': otp,
            'email':data.get("email"),
            'created_at': firestore.SERVER_TIMESTAMP,
            'expiry': expiry_time  # This will be stored as milliseconds
        })

        send_email(os.getenv('API_KEY'), otp, data.get("email"))  # Replace with actual email sending

        return jsonify({'message': f'OTP is {otp}'}), 200

    except Exception as e:
        print(f"Error: {e}")  # Log the error for debugging
        return jsonify({'error': 'An error occurred'}), 500  # Return an error response

# Example route to verify OTP
@app.route('/api/verify', methods=['POST'])
def verify_otp():
    try:
        data = request.get_json()
        email= data.get('email')
        entered_otp = data.get('otp')

        otp_data = get_otp_document(email)
    

        if otp_data is None:
             return jsonify({'error': 'OTP not found'}), 404

        else:   
            stored_otp = otp_data.get('otp')
            expiry = otp_data.get('expiry')
            print(f"stored is {stored_otp}")
            print(f"expiry {expiry}")
            expiry_datetime = datetime.datetime.fromtimestamp(expiry/1000,tz=datetime.timezone.utc)
            
            now_utc = datetime.datetime.now(datetime.timezone.utc)
           
            if expiry_datetime>now_utc: # Check Expiry
                if stored_otp == entered_otp:
                    print(f"OTP Verified")
                    create_verified_user(email=email,db=db,auth=auth)
                    return jsonify({'message': 'OTP verified successfully'}), 200
                else:
                    return jsonify({'error': 'Invalid OTP'}), 400
            else:
                
                return jsonify({'error': 'OTP expired'}), 400
           

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred'}), 500



if __name__ == '__main__':
    import datetime
    app.run(debug=True)  # Set debug=False in production