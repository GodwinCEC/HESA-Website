from app import create_app, db
from app.models import User

def add_gymncec_user():
    app = create_app()
    with app.app_context():
        # Check if gymncec already exists
        existing_user = User.query.filter_by(username='gymncec').first()
        if existing_user:
            print("User 'gymncec' already exists. Skipping...")
            return
        
        # Create gymncec user with same password as Godwin
        user = User(
            username='gymncec',
            email='gymncec@gmail.com',  # You can change this email if needed
            role='admin'  # Setting as admin to match the analytics access requirements
        )
        user.set_password('gymn748512693hesa')  # Same password as Godwin
        
        db.session.add(user)
        db.session.commit()
        
        print("Successfully added user 'gymncec' to the database!")
        print(f"Username: gymncec")
        print(f"Email: gymncec@gmail.com")
        print(f"Role: admin")
        print("Password: [same as Godwin]")

if __name__ == '__main__':
    add_gymncec_user()