"""Command line helper to create an application user."""

import argparse
from . import db

parser = argparse.ArgumentParser(description="Create a user")
parser.add_argument("username")
parser.add_argument("password")
parser.add_argument("--role", default="user")
args = parser.parse_args()

# Execute the creation and notify the operator.
db.create_user(args.username, args.password, args.role)
print(f"User {args.username} created with role {args.role}")
