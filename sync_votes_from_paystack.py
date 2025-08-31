#!/usr/bin/env python3
"""
Script to sync vote data from Paystack CSV transactions
Run this script every 12 AM after downloading the latest CSV from Paystack dashboard

Usage:
1. Download latest transactions CSV from Paystack dashboard
2. Place it in the same directory as this script
3. Update CSV_FILENAME with the correct filename
4. Run: python sync_votes_from_paystack.py
"""

import csv
import re
import os
import sys
from datetime import datetime

# Add the parent directory to Python path to import Flask app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import FohVote, AwardsVote, FohContestant, AwardsNominee

# Configuration
CSV_FILENAME = "HESA_KNUST_transactions_1756656527637.csv"  # Update this with your CSV filename
VOTE_COST = 1.0  # 1 GHS = 1 vote

def parse_csv_transactions(csv_filename):
    """Parse the Paystack CSV file and extract successful transactions"""
    if not os.path.exists(csv_filename):
        print(f"❌ Error: CSV file '{csv_filename}' not found!")
        print("Please download the latest transactions CSV from Paystack dashboard")
        return None, None
    
    foh_transactions = []
    awards_transactions = []
    
    try:
        with open(csv_filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                # Only process successful transactions
                if row['Status'].lower() != 'success':
                    continue
                
                reference = row['Reference']
                if not reference:
                    continue
                
                # Extract transaction data
                email = row['Customer (email)'] or ''
                amount = float(row['Amount Paid']) if row['Amount Paid'] else 0
                transaction_date = row['Transaction Date']
                
                # Calculate number of votes (1 GHS = 1 vote)
                votes_count = int(amount / VOTE_COST)
                if votes_count <= 0:
                    continue
                
                # Parse FOH transactions
                foh_match = re.match(r'^foh-(\d+)-', reference)
                if foh_match:
                    contestant_id = int(foh_match.group(1))
                    foh_transactions.append({
                        'contestant_id': contestant_id,
                        'email': email,
                        'votes_count': votes_count,
                        'amount': amount,
                        'transaction_ref': reference,
                        'transaction_date': transaction_date
                    })
                    continue
                
                # Parse Awards transactions
                awards_match = re.match(r'^awards-(\d+)-', reference)
                if awards_match:
                    nominee_id = int(awards_match.group(1))
                    awards_transactions.append({
                        'nominee_id': nominee_id,
                        'email': email,
                        'votes_count': votes_count,
                        'amount': amount,
                        'transaction_ref': reference,
                        'transaction_date': transaction_date
                    })
        
        print(f"✅ Successfully parsed CSV file:")
        print(f"   - FOH transactions: {len(foh_transactions)}")
        print(f"   - Awards transactions: {len(awards_transactions)}")
        
        return foh_transactions, awards_transactions
        
    except Exception as e:
        print(f"❌ Error parsing CSV file: {str(e)}")
        return None, None

def clear_existing_votes():
    """Clear existing vote data from both tables"""
    try:
        # Clear FOH votes
        foh_deleted = db.session.query(FohVote).delete()
        print(f"🗑️  Cleared {foh_deleted} existing FOH votes")
        
        # Clear Awards votes
        awards_deleted = db.session.query(AwardsVote).delete()
        print(f"🗑️  Cleared {awards_deleted} existing Awards votes")
        
        db.session.commit()
        return True
        
    except Exception as e:
        print(f"❌ Error clearing existing votes: {str(e)}")
        db.session.rollback()
        return False

def populate_foh_votes(foh_transactions):
    """Populate FOH votes table with transaction data"""
    successful = 0
    failed = 0
    
    for transaction in foh_transactions:
        try:
            # Check if contestant exists
            contestant = FohContestant.query.get(transaction['contestant_id'])
            if not contestant:
                print(f"⚠️  Warning: FOH Contestant ID {transaction['contestant_id']} not found, skipping...")
                failed += 1
                continue
            
            # Create new vote record
            vote = FohVote(
                contestant_id=transaction['contestant_id'],
                email=transaction['email'],
                votes_count=transaction['votes_count'],
                amount=transaction['amount'],
                transaction_ref=transaction['transaction_ref'],
                verified=True,  # Mark as verified since it came from Paystack
                created_at=datetime.utcnow()  # Use current time since CSV date format varies
            )
            
            db.session.add(vote)
            successful += 1
            
        except Exception as e:
            print(f"❌ Error adding FOH vote {transaction['transaction_ref']}: {str(e)}")
            failed += 1
    
    try:
        db.session.commit()
        print(f"✅ Successfully added {successful} FOH votes")
        if failed > 0:
            print(f"⚠️  Failed to add {failed} FOH votes")
        return True
        
    except Exception as e:
        print(f"❌ Error committing FOH votes: {str(e)}")
        db.session.rollback()
        return False

def populate_awards_votes(awards_transactions):
    """Populate Awards votes table with transaction data"""
    successful = 0
    failed = 0
    
    for transaction in awards_transactions:
        try:
            # Check if nominee exists
            nominee = AwardsNominee.query.get(transaction['nominee_id'])
            if not nominee:
                print(f"⚠️  Warning: Awards Nominee ID {transaction['nominee_id']} not found, skipping...")
                failed += 1
                continue
            
            # Create new vote record
            vote = AwardsVote(
                nominee_id=transaction['nominee_id'],
                email=transaction['email'],
                votes_count=transaction['votes_count'],
                amount=transaction['amount'],
                transaction_ref=transaction['transaction_ref'],
                verified=True,  # Mark as verified since it came from Paystack
                created_at=datetime.utcnow()  # Use current time since CSV date format varies
            )
            
            db.session.add(vote)
            successful += 1
            
        except Exception as e:
            print(f"❌ Error adding Awards vote {transaction['transaction_ref']}: {str(e)}")
            failed += 1
    
    try:
        db.session.commit()
        print(f"✅ Successfully added {successful} Awards votes")
        if failed > 0:
            print(f"⚠️  Failed to add {failed} Awards votes")
        return True
        
    except Exception as e:
        print(f"❌ Error committing Awards votes: {str(e)}")
        db.session.rollback()
        return False

def main():
    """Main function to sync votes from Paystack CSV"""
    print("🚀 Starting Paystack votes synchronization...")
    print(f"📁 Looking for CSV file: {CSV_FILENAME}")
    
    # Create Flask app context
    app = create_app()
    with app.app_context():
        # Step 1: Parse CSV transactions
        foh_transactions, awards_transactions = parse_csv_transactions(CSV_FILENAME)
        if foh_transactions is None or awards_transactions is None:
            return False
        
        # Step 2: Clear existing votes
        print("\n🧹 Clearing existing vote data...")
        if not clear_existing_votes():
            return False
        
        # Step 3: Populate FOH votes
        print("\n👑 Populating FOH votes...")
        if not populate_foh_votes(foh_transactions):
            return False
        
        # Step 4: Populate Awards votes
        print("\n🏆 Populating Awards votes...")
        if not populate_awards_votes(awards_transactions):
            return False
        
        print("\n🎉 Vote synchronization completed successfully!")
        print("📝 Next step: Run 'update_vote_counts.py' to update contestant/nominee vote totals")
        return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Synchronization failed!")
        sys.exit(1)
    else:
        print("\n✅ Synchronization successful!")
        sys.exit(0)