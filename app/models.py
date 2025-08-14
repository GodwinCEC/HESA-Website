from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# In models.py, update the User class to include a driver role option

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    # Update role options to include 'driver'
    role = db.Column(db.String(20), default='student')  # Options: student, admin, editor, driver
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('BlogPost', backref='author', lazy=True)
    # Add relationship for bus assignments
    bus_assignments = db.relationship('BusLocation', backref='driver', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role}')"

# Update BusLocation model to include driver relationship
class BusLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bus_id = db.Column(db.String(20), nullable=False)
    route = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    last_update = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='inactive')  # 'active', 'inactive', 'maintenance'
    # Add driver_id to link with the user who's driving the bus
    driver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    def __repr__(self):
        return f"BusLocation('{self.bus_id}', '{self.route}', '{self.last_update}')"
    
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    image_file = db.Column(db.String(256), nullable=True, default='default_blog.jpg')
    category = db.Column(db.String(20), nullable=False)
    excerpt = db.Column(db.String(200))
    read_time = db.Column(db.Integer, default=5)  # estimated reading time in minutes
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    comments = db.relationship('Comment', backref='post', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"BlogPost('{self.title}', '{self.date_posted}')"

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Can be null for anonymous comments
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)
    
    # Relationship to get commenter info
    user = db.relationship('User', foreign_keys=[user_id])
    
    def __repr__(self):
        return f"Comment('{self.content[:15]}...', '{self.date_posted}')"

class PersonalityOfTheWeek(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(256), nullable=False, default='default_potw.jpg')
    school = db.Column(db.String(100))
    year = db.Column(db.String(20))
    high_school = db.Column(db.String(100))
    quote = db.Column(db.String(200))
    # Add social media username fields (not URLs)
    twitter = db.Column(db.String(50))
    facebook = db.Column(db.String(50))
    instagram = db.Column(db.String(50))
    linkedin = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)  # Only one should be active at a time
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    comments = db.relationship('PotwComment', backref='personality', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"PersonalityOfTheWeek('{self.name}', '{self.created_at}')"

class PotwComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_name = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Foreign keys
    potw_id = db.Column(db.Integer, db.ForeignKey('personality_of_the_week.id'), nullable=False)
    
    def __repr__(self):
        return f"PotwComment('{self.author_name}', '{self.content[:15]}...', '{self.date_posted}')"

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(256), nullable=True)
    event_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"Event('{self.title}', '{self.event_date}')"


class HomeBanner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(256), nullable=False)
    order = db.Column(db.Integer, default=0)  # For ordering the banners
    is_active = db.Column(db.Boolean, default=True)  # To enable/disable banners
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"HomeBanner('{self.title}', order={self.order}, active={self.is_active})"
    
# Add to models.py

class GalleryCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    photos = db.relationship('GalleryPhoto', backref='category_ref', lazy=True)
    
    def __repr__(self):
        return f"GalleryCategory('{self.name}')"

class GalleryPhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_file = db.Column(db.String(256), nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    
    # Foreign key
    category_id = db.Column(db.Integer, db.ForeignKey('gallery_category.id'), nullable=False)
    
    def __repr__(self):
        return f"GalleryPhoto('{self.title}', '{self.date_posted}')"
    

class FohContestant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(255), nullable=False, default='default_contestant.jpg')
    votes = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FohVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contestant_id = db.Column(db.Integer, db.ForeignKey('foh_contestant.id'), nullable=False)
    email = db.Column(db.String(120), nullable=True)  # Optional voter email
    votes_count = db.Column(db.Integer, default=1)
    amount = db.Column(db.Float, nullable=False)  # Amount paid in GHS
    transaction_ref = db.Column(db.String(255), nullable=False)  # Paystack reference
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    contestant = db.relationship('FohContestant', backref='votes_received')
    
    
# Add these new models to your models.py file

class AwardsCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    nominees = db.relationship('AwardsNominee', backref='category_ref', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"AwardsCategory('{self.name}')"

class AwardsNominee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)  # Optional description
    votes = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key
    category_id = db.Column(db.Integer, db.ForeignKey('awards_category.id'), nullable=False)
    
    # Relationships
    votes_received = db.relationship('AwardsVote', backref='nominee_ref', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"AwardsNominee('{self.name}', category='{self.category_ref.name}')"

class AwardsVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nominee_id = db.Column(db.Integer, db.ForeignKey('awards_nominee.id'), nullable=False)
    email = db.Column(db.String(120), nullable=True)  # Optional voter email
    votes_count = db.Column(db.Integer, default=1)
    amount = db.Column(db.Float, nullable=False)  # Amount paid in GHS
    transaction_ref = db.Column(db.String(255), nullable=False)  # Paystack reference
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

