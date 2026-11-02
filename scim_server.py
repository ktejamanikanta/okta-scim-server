from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# The token Okta will use to authenticate to our server
API_TOKEN = os.getenv("API_TOKEN", "my_super_secret_scim_token")

# A fake in-memory database
users_db = {}

# Helper function to check authentication
def check_auth():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return False
        
    # Handle both "Bearer TOKEN" and just "TOKEN" formats
    if auth_header == API_TOKEN or auth_header == f"Bearer {API_TOKEN}":
        return True
        
    return False

# SCIM Endpoint 1: Advertise Capabilities
@app.route('/scim/v2/ServiceProviderConfig', methods=['GET'])
def service_provider_config():
    if not check_auth(): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
        "patch": {"supported": True},
        "bulk": {"supported": False, "maxOperations": 0, "maxPayloadSize": 0},
        "filter": {"supported": True, "maxResults": 200},
        "changePassword": {"supported": False},
        "sort": {"supported": False},
        "etag": {"supported": False}
    })

# SCIM Endpoint 2: Create User (POST) & List/Search Users (GET)
@app.route('/scim/v2/Users', methods=['GET', 'POST'])
def users():
    if not check_auth(): return jsonify({"error": "Unauthorized"}), 401

    if request.method == 'POST':
        # Okta is sending us a new user
        new_user = request.get_json()
        user_id = str(len(users_db) + 1)
        
        # Add SCIM required metadata
        new_user['id'] = user_id
        new_user['meta'] = {"resourceType": "User", "created": "2026-10-27T10:00:00Z"}
        
        users_db[user_id] = new_user
        print(f"✅ Created User: {new_user.get('userName')}")
        return jsonify(new_user), 201

    if request.method == 'GET':
        # DIAGNOSTIC: Print the exact URL Okta is requesting
        print(f"📥 Received GET request for: {request.url}")
        
        filter_param = request.args.get('filter')
        
        # If Okta is searching by username
        if filter_param and 'userName eq' in filter_param:
            # Extract the email from the filter string
            username_to_find = filter_param.split('"')[1]
            print(f"🔍 Okta is searching for: {username_to_find}")
            
            # Search our database
            results = [u for u in users_db.values() if u.get('userName') == username_to_find]
            response_data = {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "totalResults": len(results),
                "startIndex": 1,
                "itemsPerPage": len(results),
                "Resources": results
            }
        else:
            # If no filter (Okta's connection test), return a properly formatted list
            response_data = {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "totalResults": len(users_db),
                "startIndex": 1,
                "itemsPerPage": len(users_db),
                "Resources": list(users_db.values())
            }
            
        # DIAGNOSTIC: Print the exact JSON we are sending back to Okta
        print(f"📤 Sending response: {response_data}")
        return jsonify(response_data)

# SCIM Endpoint 3: Update / Deactivate User (PATCH)
@app.route('/scim/v2/Users/<user_id>', methods=['PATCH'])
def patch_user(user_id):
    if not check_auth(): return jsonify({"error": "Unauthorized"}), 401
    if user_id not in users_db: return jsonify({"error": "User not found"}), 404

    patch_data = request.get_json()
    user = users_db[user_id]

    # Okta sends PATCH requests to deactivate users (active: false)
    try:
        operations = patch_data.get('Operations', [])
        for op in operations:
            if op.get('path') == 'active':
                user['active'] = op.get('value')
                print(f"🔄 Updated User {user.get('userName')} - Active: {user['active']}")
    except Exception as e:
        print(f"Error parsing PATCH: {e}")

    return jsonify(user), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)