from app import create_app, db
from app.models import AwardsNominee, AwardsVote
import secrets

def add_second_votes():
    app = create_app()
    with app.app_context():
        # Find nominees who currently have exactly 1 verified vote
        nominees_with_one_vote = []
        
        for nominee in AwardsNominee.query.all():
            verified_count = db.session.query(db.func.sum(AwardsVote.votes_count)).filter(
                AwardsVote.nominee_id == nominee.id,
                AwardsVote.verified == True
            ).scalar() or 0
            
            if verified_count == 1:
                nominees_with_one_vote.append(nominee)
        
        print(f"Found {len(nominees_with_one_vote)} nominees with exactly 1 verified vote")
        
        created_count = 0
        for nominee in nominees_with_one_vote:
            # Create a second verified vote
            vote = AwardsVote(
                nominee_id=nominee.id,
                email='boost@hesa.knust.edu.gh',
                votes_count=1,
                amount=1.0,
                transaction_ref=f"boost-{nominee.id}-{secrets.token_hex(4)}",
                verified=True
            )
            
            db.session.add(vote)
            
            # Update nominee count
            nominee.votes += 1
            
            print(f"Added second vote for: {nominee.name} (now has 2 votes)")
            created_count += 1
        
        db.session.commit()
        print(f"Successfully created {created_count} additional votes!")

if __name__ == '__main__':
    add_second_votes()