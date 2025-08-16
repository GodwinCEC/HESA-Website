# Create a new file: fix_vote_counts.py in your project root
# Run this script to fix existing vote counts

from app import create_app, db
from app.models import AwardsNominee, AwardsVote

def fix_nominee_vote_counts():
    """Recalculate all nominee vote counts based only on verified votes"""
    
    app = create_app()
    with app.app_context():
        print("Starting vote count fix...")
        
        # Get all nominees
        nominees = AwardsNominee.query.all()
        
        for nominee in nominees:
            # Calculate correct vote count from verified votes only
            verified_votes = db.session.query(db.func.sum(AwardsVote.votes_count)).filter(
                AwardsVote.nominee_id == nominee.id,
                AwardsVote.verified == True
            ).scalar() or 0
            
            old_count = nominee.votes
            nominee.votes = verified_votes
            
            print(f"Nominee: {nominee.name}")
            print(f"  Old count: {old_count}")
            print(f"  New count (verified only): {verified_votes}")
            print(f"  Difference: {old_count - verified_votes}")
            print()
        
        # Commit all changes
        db.session.commit()
        print("Vote counts have been fixed successfully!")
        
        # Summary
        print("\n=== SUMMARY ===")
        total_verified_votes = db.session.query(db.func.sum(AwardsVote.votes_count)).filter(
            AwardsVote.verified == True
        ).scalar() or 0
        
        total_unverified_votes = db.session.query(db.func.sum(AwardsVote.votes_count)).filter(
            AwardsVote.verified == False
        ).scalar() or 0
        
        print(f"Total verified votes in system: {total_verified_votes}")
        print(f"Total unverified votes in system: {total_unverified_votes}")
        print(f"Total nominees updated: {len(nominees)}")

if __name__ == "__main__":
    fix_nominee_vote_counts()