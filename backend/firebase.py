import firebase_admin
from firebase_admin import credentials

def init_firebase():
    """
    Initialize Firebase Admin SDK for server-side verification and database access.
    
    1. Go to Firebase Console -> Project Settings -> Service Accounts
    2. Click 'Generate new private key'
    3. Save the downloaded JSON file to your backend directory (DO NOT commit it to git!)
    4. Uncomment the code below and point it to the file path.
    """
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK initialized successfully.")
    except ValueError:
        # This handles the case where the app is already initialized
        pass
    except Exception as e:
        print(f"Error initializing Firebase Admin SDK: {e}")
