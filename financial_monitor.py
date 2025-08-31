#!/usr/bin/env python3
"""
HESA Financial Monitoring Script
Provides comprehensive financial analytics for FOH and Awards voting

Usage: python financial_monitor.py [--detailed] [--export]
Options:
  --detailed    Show detailed breakdown by contestant/nominee
  --export      Export data to CSV files
"""

import argparse
import csv
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy import func

# Add the parent directory to Python path to import Flask app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import FohVote, AwardsVote, FohContestant, AwardsNominee, AwardsCategory

class FinancialMonitor:
    def __init__(self):
        self.foh_data = {}
        self.awards_data = {}
        self.total_revenue = 0
        self.vote_cost = 1.0  # GHS per vote
        
    def calculate_foh_financials(self):
        """Calculate FOH financial data"""
        print("👑 FACE OF HESA (IDEAL CEO) FINANCIALS")
        print("=" * 50)
        
        # Get all FOH votes
        foh_votes = db.session.query(
            FohVote.contestant_id,
            func.sum(FohVote.votes_count).label('total_votes'),
            func.sum(FohVote.amount).label('total_amount'),
            func.count(FohVote.id).label('transaction_count')
        ).filter(FohVote.verified == True)\
         .group_by(FohVote.contestant_id)\
         .all()
        
        foh_total_revenue = 0
        foh_total_votes = 0
        foh_total_transactions = 0
        
        contestant_data = []
        
        for vote_data in foh_votes:
            contestant = FohContestant.query.get(vote_data.contestant_id)
            if contestant:
                revenue = float(vote_data.total_amount)
                foh_total_revenue += revenue
                foh_total_votes += vote_data.total_votes
                foh_total_transactions += vote_data.transaction_count
                
                contestant_data.append({
                    'id': contestant.id,
                    'name': contestant.name,
                    'votes': vote_data.total_votes,
                    'revenue': revenue,
                    'transactions': vote_data.transaction_count,
                    'avg_per_transaction': revenue / vote_data.transaction_count if vote_data.transaction_count > 0 else 0
                })
        
        # Sort by revenue
        contestant_data.sort(key=lambda x: x['revenue'], reverse=True)
        
        print(f"💰 Total Revenue: GH₵ {foh_total_revenue:,.2f}")
        print(f"🗳️  Total Votes: {foh_total_votes:,}")
        print(f"📊 Total Transactions: {foh_total_transactions:,}")
        print(f"💳 Average per Transaction: GH₵ {foh_total_revenue / foh_total_transactions if foh_total_transactions > 0 else 0:.2f}")
        
        # Top performers
        if contestant_data:
            print(f"\n🏆 TOP EARNING CONTESTANTS:")
            for i, contestant in enumerate(contestant_data[:5], 1):
                percentage = (contestant['revenue'] / foh_total_revenue * 100) if foh_total_revenue > 0 else 0
                print(f"   {i}. {contestant['name']}: GH₵ {contestant['revenue']:.2f} ({percentage:.1f}%)")
        
        self.foh_data = {
            'total_revenue': foh_total_revenue,
            'total_votes': foh_total_votes,
            'total_transactions': foh_total_transactions,
            'contestants': contestant_data
        }
        
        return foh_total_revenue
    
    def calculate_awards_financials(self):
        """Calculate Awards financial data"""
        print("\n🏆 HESA AWARDS FINANCIALS")
        print("=" * 50)
        
        # Get all Awards votes with category info
        awards_votes = db.session.query(
            AwardsVote.nominee_id,
            func.sum(AwardsVote.votes_count).label('total_votes'),
            func.sum(AwardsVote.amount).label('total_amount'),
            func.count(AwardsVote.id).label('transaction_count')
        ).filter(AwardsVote.verified == True)\
         .group_by(AwardsVote.nominee_id)\
         .all()
        
        awards_total_revenue = 0
        awards_total_votes = 0
        awards_total_transactions = 0
        
        nominee_data = []
        category_revenue = defaultdict(float)
        
        for vote_data in awards_votes:
            nominee = AwardsNominee.query.get(vote_data.nominee_id)
            if nominee:
                revenue = float(vote_data.total_amount)
                awards_total_revenue += revenue
                awards_total_votes += vote_data.total_votes
                awards_total_transactions += vote_data.transaction_count
                
                category_name = nominee.category_ref.name if nominee.category_ref else "Unknown"
                category_revenue[category_name] += revenue
                
                nominee_data.append({
                    'id': nominee.id,
                    'name': nominee.name,
                    'category': category_name,
                    'votes': vote_data.total_votes,
                    'revenue': revenue,
                    'transactions': vote_data.transaction_count,
                    'avg_per_transaction': revenue / vote_data.transaction_count if vote_data.transaction_count > 0 else 0
                })
        
        # Sort by revenue
        nominee_data.sort(key=lambda x: x['revenue'], reverse=True)
        
        print(f"💰 Total Revenue: GH₵ {awards_total_revenue:,.2f}")
        print(f"🗳️  Total Votes: {awards_total_votes:,}")
        print(f"📊 Total Transactions: {awards_total_transactions:,}")
        print(f"💳 Average per Transaction: GH₵ {awards_total_revenue / awards_total_transactions if awards_total_transactions > 0 else 0:.2f}")
        
        # Category breakdown
        if category_revenue:
            print(f"\n📈 REVENUE BY CATEGORY:")
            sorted_categories = sorted(category_revenue.items(), key=lambda x: x[1], reverse=True)
            for category, revenue in sorted_categories:
                percentage = (revenue / awards_total_revenue * 100) if awards_total_revenue > 0 else 0
                print(f"   {category}: GH₵ {revenue:.2f} ({percentage:.1f}%)")
        
        # Top performers
        if nominee_data:
            print(f"\n🏆 TOP EARNING NOMINEES:")
            for i, nominee in enumerate(nominee_data[:5], 1):
                percentage = (nominee['revenue'] / awards_total_revenue * 100) if awards_total_revenue > 0 else 0
                print(f"   {i}. {nominee['name']} ({nominee['category']}): GH₵ {nominee['revenue']:.2f} ({percentage:.1f}%)")
        
        self.awards_data = {
            'total_revenue': awards_total_revenue,
            'total_votes': awards_total_votes,
            'total_transactions': awards_total_transactions,
            'nominees': nominee_data,
            'category_revenue': dict(category_revenue)
        }
        
        return awards_total_revenue
    
    def show_detailed_breakdown(self):
        """Show detailed breakdown of all contestants and nominees"""
        print("\n" + "=" * 70)
        print("📊 DETAILED FINANCIAL BREAKDOWN")
        print("=" * 70)
        
        # FOH Detailed
        print("\n👑 FOH CONTESTANTS (All):")
        print("-" * 40)
        if self.foh_data['contestants']:
            for contestant in self.foh_data['contestants']:
                print(f"ID {contestant['id']:2d} | {contestant['name']:<25} | "
                      f"GH₵ {contestant['revenue']:8.2f} | "
                      f"{contestant['votes']:4d} votes | "
                      f"{contestant['transactions']:3d} txns")
        else:
            print("   No FOH data available")
        
        # Awards Detailed by Category
        print("\n🏆 AWARDS NOMINEES (By Category):")
        print("-" * 50)
        
        if self.awards_data['nominees']:
            # Group by category
            by_category = defaultdict(list)
            for nominee in self.awards_data['nominees']:
                by_category[nominee['category']].append(nominee)
            
            for category, nominees in by_category.items():
                print(f"\n📂 {category.upper()}:")
                for nominee in nominees:
                    print(f"   ID {nominee['id']:2d} | {nominee['name']:<25} | "
                          f"GH₵ {nominee['revenue']:8.2f} | "
                          f"{nominee['votes']:4d} votes | "
                          f"{nominee['transactions']:3d} txns")
        else:
            print("   No Awards data available")
    
    def export_to_csv(self):
        """Export financial data to CSV files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export FOH data
        foh_filename = f"foh_financial_report_{timestamp}.csv"
        with open(foh_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', 'name', 'votes', 'revenue', 'transactions', 'avg_per_transaction']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.foh_data['contestants'])
        
        print(f"📄 FOH report exported: {foh_filename}")
        
        # Export Awards data
        awards_filename = f"awards_financial_report_{timestamp}.csv"
        with open(awards_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', 'name', 'category', 'votes', 'revenue', 'transactions', 'avg_per_transaction']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.awards_data['nominees'])
        
        print(f"📄 Awards report exported: {awards_filename}")
        
        # Export summary
        summary_filename = f"financial_summary_{timestamp}.csv"
        with open(summary_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Metric', 'FOH', 'Awards', 'Total'])
            writer.writerow(['Revenue (GHS)', 
                           f"{self.foh_data['total_revenue']:.2f}",
                           f"{self.awards_data['total_revenue']:.2f}",
                           f"{self.total_revenue:.2f}"])
            writer.writerow(['Total Votes',
                           self.foh_data['total_votes'],
                           self.awards_data['total_votes'],
                           self.foh_data['total_votes'] + self.awards_data['total_votes']])
            writer.writerow(['Total Transactions',
                           self.foh_data['total_transactions'],
                           self.awards_data['total_transactions'],
                           self.foh_data['total_transactions'] + self.awards_data['total_transactions']])
        
        print(f"📄 Summary report exported: {summary_filename}")
    
    def show_summary(self):
        """Show overall financial summary"""
        foh_revenue = self.calculate_foh_financials()
        awards_revenue = self.calculate_awards_financials()
        self.total_revenue = foh_revenue + awards_revenue
        
        print("\n" + "=" * 70)
        print("💎 OVERALL FINANCIAL SUMMARY")
        print("=" * 70)
        
        total_votes = self.foh_data['total_votes'] + self.awards_data['total_votes']
        total_transactions = self.foh_data['total_transactions'] + self.awards_data['total_transactions']
        
        print(f"🏆 Grand Total Revenue: GH₵ {self.total_revenue:,.2f}")
        print(f"🗳️  Grand Total Votes: {total_votes:,}")
        print(f"📊 Grand Total Transactions: {total_transactions:,}")
        
        if self.total_revenue > 0:
            foh_percentage = (foh_revenue / self.total_revenue) * 100
            awards_percentage = (awards_revenue / self.total_revenue) * 100
            
            print(f"\n📈 Revenue Split:")
            print(f"   FOH (Ideal CEO): GH₵ {foh_revenue:,.2f} ({foh_percentage:.1f}%)")
            print(f"   Awards: GH₵ {awards_revenue:,.2f} ({awards_percentage:.1f}%)")
        
        avg_transaction = self.total_revenue / total_transactions if total_transactions > 0 else 0
        print(f"\n💳 Average Transaction: GH₵ {avg_transaction:.2f}")
        
        # Potential earnings projection
        if total_votes > 0:
            print(f"\n🎯 Performance Metrics:")
            print(f"   Vote-to-Revenue Ratio: 1 vote = GH₵ {self.total_revenue / total_votes:.2f}")
            print(f"   Transaction Efficiency: {total_votes / total_transactions:.1f} votes per transaction")

def main():
    parser = argparse.ArgumentParser(description='HESA Financial Monitor')
    parser.add_argument('--detailed', action='store_true', help='Show detailed breakdown')
    parser.add_argument('--export', action='store_true', help='Export data to CSV files')
    args = parser.parse_args()
    
    print("💰 HESA FINANCIAL MONITORING SYSTEM")
    print("=" * 70)
    print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create Flask app context
    app = create_app()
    with app.app_context():
        monitor = FinancialMonitor()
        
        # Show main summary
        monitor.show_summary()
        
        # Show detailed breakdown if requested
        if args.detailed:
            monitor.show_detailed_breakdown()
        
        # Export to CSV if requested
        if args.export:
            print("\n📋 EXPORTING DATA...")
            monitor.export_to_csv()
        
        print("\n" + "=" * 70)
        print("✅ Financial monitoring complete!")
        
        if not args.detailed:
            print("💡 Tip: Use --detailed for complete breakdown")
        if not args.export:
            print("💡 Tip: Use --export to save data to CSV files")

if __name__ == "__main__":
    main()