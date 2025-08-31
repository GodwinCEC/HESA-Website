#!/usr/bin/env python3
"""
Script to update vote counts for FOH contestants and Awards nominees
Run this script AFTER sync_votes_from_paystack.py

This script calculates the total votes for each contestant/nominee 
by summing up verified votes from the votes tables.

Usage: python update_vote_counts.py
"""

import os
import sys
from sqlalchemy import func

# Add the parent directory to Python path to import Flask app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import FohVote, AwardsVote, FohContestant, AwardsNominee

def update_foh_vote_counts():
    """Update vote counts for all FOH contestants"""
    try:
        print("👑 Updating FOH contestant vote counts...")
        
        # Get all contestants
        contestants = FohContestant.query.all()
        updated_count = 0
        
        for contestant in contestants:
            # Calculate total verified votes for this contestant
            total_votes = db.session.query(func.sum(FohVote.votes_count))\
                .filter(FohVote.contestant_id == contestant.id,
                       FohVote.verified == True)\
                .scalar() or 0
            
            # Update contestant's vote count
            old_votes = contestant.votes
            contestant.votes = int(total_votes)
            
            print(f"   Contestant {contestant.id} ({contestant.name}): {old_votes} → {contestant.votes} votes")
            updated_count += 1
        
        # Commit changes
        db.session.commit()
        print(f"✅ Updated {updated_count} FOH contestants")
        return True
        
    except Exception as e:
        print(f"❌ Error updating FOH vote counts: {str(e)}")
        db.session.rollback()
        return False

def update_awards_vote_counts():
    """Update vote counts for all Awards nominees"""
    try:
        print("🏆 Updating Awards nominee vote counts...")
        
        # Get all nominees
        nominees = AwardsNominee.query.all()
        updated_count = 0
        
        for nominee in nominees:
            # Calculate total verified votes for this nominee
            total_votes = db.session.query(func.sum(AwardsVote.votes_count))\
                .filter(AwardsVote.nominee_id == nominee.id,
                       AwardsVote.verified == True)\
                .scalar() or 0
            
            # Update nominee's vote count
            old_votes = nominee.votes
            nominee.votes = int(total_votes)
            
            category_name = nominee.category_ref.name if nominee.category_ref else "Unknown Category"
            print(f"   Nominee {nominee.id} ({nominee.name} - {category_name}): {old_votes} → {nominee.votes} votes")
            updated_count += 1
        
        # Commit changes
        db.session.commit()
        print(f"✅ Updated {updated_count} Awards nominees")
        return True
        
    except Exception as e:
        print(f"❌ Error updating Awards vote counts: {str(e)}")
        db.session.rollback()
        return False

def print_summary_stats():
    """Print summary statistics"""
    try:
        print("\n📊 Vote Count Summary:")
        
        # FOH stats
        total_foh_votes = db.session.query(func.sum(FohVote.votes_count))\
            .filter(FohVote.verified == True).scalar() or 0
        total_foh_contestants = FohContestant.query.count()
        
        print(f"👑 FOH: {total_foh_votes} total votes across {total_foh_contestants} contestants")
        
        # Awards stats
        total_awards_votes = db.session.query(func.sum(AwardsVote.votes_count))\
            .filter(AwardsVote.verified == True).scalar() or 0
        total_awards_nominees = AwardsNominee.query.count()
        
        print(f"🏆 Awards: {total_awards_votes} total votes across {total_awards_nominees} nominees")
        
        # Top performers
        print("\n🔥 Top Performers:")
        
        # Top FOH contestant
        top_foh = FohContestant.query.order_by(FohContestant.votes.desc()).first()
        if top_foh:
            print(f"   👑 FOH Leader: {top_foh.name} with {top_foh.votes} votes")
        
        # Top Awards nominee
        top_awards = AwardsNominee.query.order_by(AwardsNominee.votes.desc()).first()
        if top_awards:
            category_name = top_awards.category_ref.name if top_awards.category_ref else "Unknown"
            print(f"   🏆 Awards Leader: {top_awards.name} ({category_name}) with {top_awards.votes} votes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating summary stats: {str(e)}")
        return False

def main():
    """Main function to update all vote counts"""
    print("🔄 Starting vote count updates...")
    
    # Create Flask app context
    app = create_app()
    with app.app_context():
        
        # Step 1: Update FOH vote counts
        if not update_foh_vote_counts():
            return False
        
        print()  # Add spacing
        
        # Step 2: Update Awards vote counts
        if not update_awards_vote_counts():
            return False
        
        # Step 3: Print summary statistics
        print_summary_stats()
        
        print("\n🎉 Vote count updates completed successfully!")
        print("🌐 Website data is now synced with Paystack transactions")
        return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Vote count update failed!")
        sys.exit(1)
    else:
        print("\n✅ Vote count update successful!")
        sys.exit(0)