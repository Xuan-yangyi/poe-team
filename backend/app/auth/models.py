# MVP: hardcoded users table. Replace with real user model in production.
# For now, auth verifies against this in-memory store.
USERS = {
    "factory_admin": {
        "id": "user_factory_01",
        "username": "factory_admin",
        "password_hash": "",  # will be set in conftest
        "role": "factory_admin",
        "tenant_id": "factory",
    },
    "idh_op": {
        "id": "user_idh_01",
        "username": "idh_op",
        "password_hash": "",
        "role": "idh_op",
        "tenant_id": "IDH001",
        "idh_id": "IDH001",
    },
}