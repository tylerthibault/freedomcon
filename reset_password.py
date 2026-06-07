"""CLI tool to reset an admin user's password.

Usage:
    python reset_password.py <username> <new_password>
"""
import sys
from run import create_app

def main():
    if len(sys.argv) != 3:
        print("Usage: python reset_password.py <username> <new_password>")
        sys.exit(1)

    username, new_password = sys.argv[1], sys.argv[2]

    app = create_app()
    with app.app_context():
        from src.models.main import AdminUser, db

        user = db.session.execute(
            db.select(AdminUser).where(AdminUser.username == username)
        ).scalar_one_or_none()

        if not user:
            print(f"Error: user '{username}' not found.")
            sys.exit(1)

        user.set_password(new_password)
        db.session.commit()
        print(f"Password for '{username}' has been reset.")

if __name__ == "__main__":
    main()
