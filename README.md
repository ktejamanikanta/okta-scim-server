# 🔄 Custom SCIM 2.0 Provisioning Server (Python/Flask)

This repository contains a custom-built SCIM 2.0 (System for Cross-domain Identity Management) server. It is designed to integrate with Okta to automate the **Joiner-Mover-Leaver (JML)** user lifecycle.

While OIDC and SAML handle *authentication* (logging users in), SCIM handles *provisioning* (automatically creating, updating, and deactivating user accounts in the backend database).

## 🚀 Features
*   **User Creation (Joiner):** Handles `POST /scim/v2/Users` requests from Okta to create new user records in the database.
*   **User Search (Filtering):** Handles `GET /scim/v2/Users?filter=userName eq "..."` to prevent duplicate accounts when Okta checks if a user already exists.
*   **Deactivation (Leaver):** Handles `PATCH /scim/v2/Users/{id}` requests to set `"active": false` when an employee is terminated (Soft Delete).
*   **Security:** Protects all SCIM endpoints using Bearer Token authentication in the HTTP `Authorization` header.
*   **SCIM Schema Compliance:** Returns the standard `ListResponse` JSON schema required by Okta (`schemas`, `totalResults`, `startIndex`, `itemsPerPage`, `Resources`).

## 🛠️ Tech Stack
*   **Backend:** Python 3, Flask
*   **Protocol:** SCIM 2.0 (REST API, JSON)
*   **Tunneling:** Ngrok (to expose the localhost server to the Okta cloud)

## 🧠 Key SCIM Concepts Implemented
*   **Filtering Logic:** SCIM requires the server to parse specific query parameters (like `eq` for equals) to check if a user exists.
*   **Soft Deletes:** SCIM best practices dictate that users are rarely hard-deleted. Instead, the server handles `PATCH` requests to flip the `active` flag to `false`.
*   **ServiceProviderConfig:** Exposes a `/scim/v2/ServiceProviderConfig` endpoint to advertise server capabilities (e.g., supporting PATCH) to Okta.
*   **Authentication Handling:** Handles both `Bearer <token>` and raw `<token>` formats in the Authorization header.

## 💻 Local Setup & Testing

### 1. Clone and Install Dependencies
```bash
git clone https://github.com/ktejamanikanta/okta-scim-server.git
cd okta-scim-server
python -m venv venv
# On Windows:
venv\Scripts\activate
# Install requirements
pip install flask python-dotenv
