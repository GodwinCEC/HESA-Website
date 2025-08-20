from app import create_app, db
from app.models import AwardsNominee, AwardsVote

def undo_added_votes():
    app = create_app()
    with app.app_context():
        print("Undoing artificially added votes...")
        
        # Delete votes with our specific emails (the ones we created)
        artificial_votes = AwardsVote.query.filter(
            AwardsVote.email.in_(['analytics@hesa.knust.edu.gh', 'boost@hesa.knust.edu.gh'])
        ).all()
        
        print(f"Found {len(artificial_votes)} artificial votes to remove")
        
        # Track affected nominees
        affected_nominees = set()
        total_votes_to_subtract = {}
        
        for vote in artificial_votes:
            nominee_id = vote.nominee_id
            affected_nominees.add(nominee_id)
            
            if nominee_id not in total_votes_to_subtract:
                total_votes_to_subtract[nominee_id] = 0
            total_votes_to_subtract[nominee_id] += vote.votes_count
            
            print(f"Removing vote: {vote.transaction_ref} for nominee {vote.nominee_ref.name}")
            db.session.delete(vote)
        
        # Update nominee vote counts
        for nominee_id in affected_nominees:
            nominee = AwardsNominee.query.get(nominee_id)
            votes_to_subtract = total_votes_to_subtract[nominee_id]
            old_count = nominee.votes
            nominee.votes = max(0, nominee.votes - votes_to_subtract)  # Don't go below 0
            
            print(f"Updated {nominee.name}: {old_count} -> {nominee.votes} votes")
        
        db.session.commit()
        print(f"Successfully undone artificial votes for {len(affected_nominees)} nominees!")
        
        # Show final status
        print("\nFinal vote counts:")
        for nominee_id in affected_nominees:
            nominee = AwardsNominee.query.get(nominee_id)
            real_verified_count = db.session.query(db.func.sum(AwardsVote.votes_count)).filter(
                AwardsVote.nominee_id == nominee.id,
                AwardsVote.verified == True
            ).scalar() or 0
            print(f"{nominee.name}: stored={nominee.votes}, verified_in_db={real_verified_count}")

if __name__ == '__main__':
    undo_added_votes()