from getpass import getpass

from app import app
from models import db, User


def create_hr_account():
    with app.app_context():

        print("\n--- SmartHR: Create HR Account ---\n")

        name = input("Enter HR name: ").strip()
        email = input("Enter HR email: ").strip().lower()
        password = getpass("Enter HR password: ")
        confirm_password = getpass("Confirm password: ")

        if not name or not email or not password:
            print("\nAll fields are required.")
            return

        if len(password) < 8:
            print("\nPassword must contain at least 8 characters.")
            return

        if password != confirm_password:
            print("\nPasswords do not match.")
            return

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            print("\nAn account with this email already exists.")
            return

        hr_user = User(
            name=name,
            email=email,
            role="hr"
        )

        hr_user.set_password(password)

        db.session.add(hr_user)
        db.session.commit()

        print("\nHR account created successfully!")
        print("You can now log in to SmartHR.")


if __name__ == "__main__":
    create_hr_account()