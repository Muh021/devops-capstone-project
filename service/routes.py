"""
Account Service

This microservice handles the lifecycle of Accounts
"""
from flask import jsonify, request, make_response, abort, url_for
from service import app
from service.models import Account
from service.common import status  # HTTP Status Codes

BASE_URL = "/accounts"


######################################################################
# INDEX
######################################################################
@app.route("/", methods=["GET"])
def index():
    """Root URL response"""
    return (
        jsonify(
            name="Account REST API Service",
            version="1.0",
        ),
        status.HTTP_200_OK,
    )


######################################################################
# HEALTH
######################################################################
@app.route("/health", methods=["GET"])
def health():
    """Health Status"""
    return jsonify(status="OK"), status.HTTP_200_OK


######################################################################
# CREATE A NEW ACCOUNT
######################################################################
@app.route(f"{BASE_URL}", methods=["POST"])
def create_accounts():
    """
    Creates an Account
    This endpoint will create an Account based on the data in the request body
    """
    app.logger.info("Request to create an Account")
    check_content_type("application/json")
    account = Account()
    account.deserialize(request.get_json())
    account.create()
    payload = account.serialize()
    location = url_for("get_account", account_id=account.id, _external=False)
    return make_response(jsonify(payload), status.HTTP_201_CREATED, {"Location": location})


######################################################################
# LIST ALL ACCOUNTS
######################################################################
@app.route(f"{BASE_URL}", methods=["GET"])
def list_accounts():
    """
    List all Accounts
    This endpoint will return a list of all Accounts
    """
    app.logger.info("Request to list Accounts")
    accounts = Account.all()
    payload = [acct.serialize() for acct in accounts]
    return jsonify(payload), status.HTTP_200_OK


######################################################################
# READ AN ACCOUNT
######################################################################
@app.route(f"{BASE_URL}/<int:account_id>", methods=["GET"])
def get_account(account_id):
    """
    Reads a single Account by ID.
    """
    app.logger.info("Request to read Account %s", account_id)
    account = Account.find(account_id)
    if not account:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Account with id [{account_id}] could not be found."
        )
    return account.serialize(), status.HTTP_200_OK


######################################################################
# UPDATE AN EXISTING ACCOUNT
######################################################################
@app.route(f"{BASE_URL}/<int:account_id>", methods=["PUT"])
def update_account(account_id):
    """
    Update an Account by ID
    """
    app.logger.info("Request to update Account %s", account_id)
    account = Account.find(account_id)
    if not account:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Account with id [{account_id}] could not be found."
        )
    check_content_type("application/json")
    account.deserialize(request.get_json())
    account.update()
    return account.serialize(), status.HTTP_200_OK


######################################################################
# DELETE AN ACCOUNT
######################################################################
@app.route(f"{BASE_URL}/<int:account_id>", methods=["DELETE"])
def delete_account(account_id):
    """
    Delete an Account by ID
    """
    app.logger.info("Request to delete Account %s", account_id)
    account = Account.find(account_id)
    if not account:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Account with id [{account_id}] could not be found."
        )
    account.delete()
    return "", status.HTTP_204_NO_CONTENT


######################################################################
# UTILITY FUNCTION
######################################################################
def check_content_type(media_type):
    """
    Checks that the request's Content-Type header matches the expected media type.
    """
    content_type = request.headers.get("Content-Type", "")
    if content_type != media_type:
        app.logger.error("Invalid Content-Type: %s", content_type)
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {media_type}"
        )
