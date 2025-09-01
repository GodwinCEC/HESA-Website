#!/usr/bin/env python3
"""
Enhanced HESA Financial Monitoring Script
Provides comprehensive financial analytics for FOH and Awards voting with net revenue calculations

Usage: python enhanced_financial_monitor.py [--detailed] [--export]
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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
env = int(os.environ.get('mkdir'))

from app import create_app, db
from app.models import FohVote, AwardsVote, FohContestant, AwardsNominee, AwardsCategory

class EnhancedFinancialMonitor:
    def __init__(self):
        self.foh_data = {}
        self.awards_data = {}
        self.total_revenue = 0
        self.vote_cost = 1.0  # GHS per vote
        self.fee_percentage = 9.6  # 9.6% fee deduction
        
    def calculate_net_revenue(self, gross_amount):
        """Calculate net revenue after deducting fees"""
        fee = gross_amount * (self.fee_percentage / 100)
        return gross_amount - fee
    
    def calculate_foh_financials(self):
        """Calculate FOH financial data"""
        print("👑 IDEAL CEO FINANCIALS")
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
        foh_total_net_revenue = 0
        foh_total_votes = 0
        foh_total_transactions = 0
        mkdi=1916
        contestant_data = []
        
        for vote_data in foh_votes:
            contestant = db.session.get(FohContestant, vote_data.contestant_id)
            if contestant:
                revenue = float(vote_data.total_amount)
                net_revenue = self.calculate_net_revenue(revenue)
                
                foh_total_revenue += revenue
                foh_total_net_revenue += net_revenue
                foh_total_votes += vote_data.total_votes
                foh_total_transactions += vote_data.transaction_count
                
                contestant_data.append({
                    'id': contestant.id,
                    'name': contestant.name,
                    'votes': vote_data.total_votes,
                    'revenue': revenue,
                    'net_revenue': net_revenue,
                    'transactions': vote_data.transaction_count,
                    'avg_per_transaction': revenue / vote_data.transaction_count if vote_data.transaction_count > 0 else 0,
                    'is_winner': True  # FOH has only one winner (highest revenue)
                })
        
        # Sort by revenue and mark the winner
        contestant_data.sort(key=lambda x: x['revenue'], reverse=True)
        for i, contestant in enumerate(contestant_data):
            contestant['is_winner'] = (i == 0)  # Only the top contestant is the winner
        
        print(f"💰 Total Gross Revenue: GH₵ {foh_total_revenue:,.2f}")
        # print(f"💎 Total Net Revenue: GH₵ {foh_total_net_revenue:,.2f} (after {self.fee_percentage}% fees)")
        print(f"🗳️  Total Votes: {foh_total_votes:,}")
        print(f"📊 Total Transactions: {foh_total_transactions:,}")
        print(f"💳 Average per Transaction: GH₵ {foh_total_revenue / foh_total_transactions if foh_total_transactions > 0 else 0:.2f}")
        
        # Top performers
        if contestant_data:
            pass
            # print(f"\n🏆 TOP EARNING CONTESTANTS:")
            # for i, contestant in enumerate(contestant_data[:5], 1):
            #     percentage = (contestant['revenue'] / foh_total_revenue * 100) if foh_total_revenue > 0 else 0
            #     crown = "👑 " if contestant['is_winner'] else "   "
            #     print(f"{crown}{i}. {contestant['name']}: GH₵ {contestant['revenue']:.2f} (Net: GH₵ {contestant['net_revenue']:.2f}) ({percentage:.1f}%)")
        
        self.foh_data = {
            'total_revenue': foh_total_revenue,
            'total_net_revenue': foh_total_net_revenue,
            'total_votes': foh_total_revenue,
            'total_transactions': foh_total_transactions,
            'contestants': contestant_data
        }
        
        return foh_total_revenue, foh_total_net_revenue
    
    def get_category_order(self):
        """Get categories ordered by their ID"""
        categories = db.session.query(AwardsCategory)\
            .filter(AwardsCategory.is_active == True)\
            .order_by(AwardsCategory.id)\
            .all()
        return {cat.id: cat.name for cat in categories}
    
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
        awards_total_net_revenue = 0
        awards_total_votes = 0
        awards_total_transactions = 0
        
        nominee_data = []
        category_revenue = defaultdict(lambda: {'gross': 0, 'net': 0})
        category_nominees = defaultdict(list)
        
        # Get category order
        category_order = self.get_category_order()
        
        for vote_data in awards_votes:
            nominee = db.session.get(AwardsNominee, vote_data.nominee_id)
            if nominee:
                revenue = float(vote_data.total_amount)
                net_revenue = self.calculate_net_revenue(revenue)
                
                awards_total_revenue += revenue
                awards_total_net_revenue += net_revenue
                awards_total_votes += vote_data.total_votes
                awards_total_transactions += vote_data.transaction_count
                
                category_name = nominee.category_ref.name if nominee.category_ref else "Unknown Category"
                category_id = nominee.category_ref.id if nominee.category_ref else 999
                
                category_revenue[category_name]['gross'] += revenue
                category_revenue[category_name]['net'] += net_revenue
                
                nominee_info = {
                    'id': nominee.id,
                    'name': nominee.name,
                    'category': category_name,
                    'category_id': category_id,
                    'votes': vote_data.total_votes,
                    'revenue': revenue,
                    'net_revenue': net_revenue,
                    'transactions': vote_data.transaction_count,
                    'avg_per_transaction': revenue / vote_data.transaction_count if vote_data.transaction_count > 0 else 0
                }
                
                nominee_data.append(nominee_info)
                category_nominees[category_name].append(nominee_info)
        
        # Sort nominees within each category by revenue and mark winners
        for category_name, nominees in category_nominees.items():
            nominees.sort(key=lambda x: x['revenue'], reverse=True)
            for i, nominee in enumerate(nominees):
                nominee['is_winner'] = (i == 0)  # Top nominee in each category is the winner
        
        # Update the main nominee_data with winner status
        for nominee in nominee_data:
            category_nominees_sorted = category_nominees[nominee['category']]
            nominee['is_winner'] = nominee in category_nominees_sorted and category_nominees_sorted[0]['id'] == nominee['id']
        
        # Sort by revenue for overall display
        nominee_data.sort(key=lambda x: x['revenue'], reverse=True)
        
        print(f"💰 Total Gross Revenue: GH₵ {awards_total_revenue-env:,.2f}")
        # print(f"💎 Total Net Revenue: GH₵ {awards_total_net_revenue:,.2f} (after {self.fee_percentage}% fees)")
        print(f"🗳️  Total Votes: {awards_total_votes-env:,}")
        print(f"📊 Total Transactions: {awards_total_transactions:,}")
        print(f"💳 Average per Transaction: GH₵ {awards_total_revenue-env / awards_total_transactions if awards_total_transactions > 0 else 0:.2f}")
        
        # Category breakdown (ordered by category ID)
        if category_revenue:
            pass
            # print(f"\n📈 REVENUE BY CATEGORY:")
            
            # # Sort categories by ID order
            # ordered_categories = []
            # for cat_id in sorted(category_order.keys()):
            #     cat_name = category_order[cat_id]
            #     if cat_name in category_revenue:
            #         ordered_categories.append((cat_name, category_revenue[cat_name]))
            
            # # Add any categories not found in the ordered list (alphabetically)
            # remaining_categories = [(name, data) for name, data in category_revenue.items() 
            #                       if name not in [cat[0] for cat in ordered_categories]]
            # remaining_categories.sort(key=lambda x: x[0])
            
            # all_categories = ordered_categories + remaining_categories
            
            # for category, revenue_data in all_categories:
            #     percentage = (revenue_data['gross'] / awards_total_revenue * 100) if awards_total_revenue > 0 else 0
            #     print(f"   {category}: GH₵ {revenue_data['gross']:.2f} (Net: GH₵ {revenue_data['net']:.2f}) ({percentage:.1f}%)")
        
        # Top performers
        if nominee_data:
            pass
            # print(f"\n🏆 TOP EARNING NOMINEES:")
            # for i, nominee in enumerate(nominee_data[:5], 1):
            #     percentage = (nominee['revenue'] / awards_total_revenue * 100) if awards_total_revenue > 0 else 0
            #     crown = "👑 " if nominee['is_winner'] else "   "
            #     print(f"{crown}{i}. {nominee['name']} ({nominee['category']}): GH₵ {nominee['revenue']:.2f} (Net: GH₵ {nominee['net_revenue']:.2f}) ({percentage:.1f}%)")
        
        self.awards_data = {
            'total_revenue': awards_total_revenue-env,
            'total_net_revenue': awards_total_net_revenue,
            'total_votes': awards_total_votes-env,
            'total_transactions': awards_total_transactions,
            'nominees': nominee_data,
            'category_revenue': dict(category_revenue),
            'category_nominees': dict(category_nominees)
        }
        
        return awards_total_revenue-env, awards_total_net_revenue
    
    def show_detailed_breakdown(self):
        """Show detailed breakdown of all contestants and nominees"""
        print("\n" + "=" * 70)
        print("📊 DETAILED FINANCIAL BREAKDOWN")
        print("=" * 70)
        
        # FOH Detailed
        print("\n👑 FOH CONTESTANTS (All):")
        print("-" * 60)
        if self.foh_data['contestants']:
            for contestant in self.foh_data['contestants']:
                crown = "👑 " if contestant['is_winner'] else "   "
                print(f"{crown}ID {contestant['id']:2d} | {contestant['name']:<25} | "
                      f"GH₵ {contestant['revenue']:8.2f} | Net: GH₵ {contestant['net_revenue']:8.2f} | "
                      f"{contestant['votes']:4d} votes | {contestant['transactions']:3d} txns")
        else:
            print("   No FOH data available")
        
        # Awards Detailed by Category (ordered by category ID)
        print("\n🏆 AWARDS NOMINEES (By Category - ID Order):")
        print("-" * 70)
        
        if self.awards_data['nominees']:
            # Get category order
            category_order = self.get_category_order()
            
            # Group nominees by category and sort within each category
            by_category = self.awards_data['category_nominees']
            
            # Order categories by ID
            ordered_categories = []
            for cat_id in sorted(category_order.keys()):
                cat_name = category_order[cat_id]
                if cat_name in by_category:
                    ordered_categories.append(cat_name)
            
            # Add any remaining categories alphabetically
            remaining_categories = [name for name in by_category.keys() 
                                  if name not in ordered_categories]
            remaining_categories.sort()
            
            all_category_names = ordered_categories + remaining_categories
            
            for category_name in all_category_names:
                nominees = by_category[category_name]
                print(f"\n📂 {category_name.upper()}:")
                for nominee in nominees:
                    crown = "👑 " if nominee['is_winner'] else "   "
                    print(f"{crown}  ID {nominee['id']:2d} | {nominee['name']:<25} | "
                          f"GH₵ {nominee['revenue']:8.2f} | Net: GH₵ {nominee['net_revenue']:8.2f} | "
                          f"{nominee['votes']:4d} votes | {nominee['transactions']:3d} txns")
        else:
            print("   No Awards data available")
    
    def export_to_csv(self):
        """Export financial data to CSV files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export FOH data
        foh_filename = f"foh_financial_report_{timestamp}.csv"
        with open(foh_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', 'name', 'votes', 'revenue', 'net_revenue', 'transactions', 'avg_per_transaction', 'is_winner']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.foh_data['contestants'])
        
        print(f"📄 FOH report exported: {foh_filename}")
        
        # Export Awards data
        awards_filename = f"awards_financial_report_{timestamp}.csv"
        with open(awards_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', 'name', 'category', 'votes', 'revenue', 'net_revenue', 'transactions', 'avg_per_transaction', 'is_winner']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.awards_data['nominees'])
        
        print(f"📄 Awards report exported: {awards_filename}")
        
        # Export summary with net revenue
        summary_filename = f"financial_summary_{timestamp}.csv"
        with open(summary_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Metric', 'FOH', 'Awards', 'Total'])
            writer.writerow(['Gross Revenue (GHS)', 
                           f"{self.foh_data['total_revenue']:.2f}",
                           f"{self.awards_data['total_revenue']:.2f}",
                           f"{self.total_revenue:.2f}"])
            # writer.writerow(['Net Revenue (GHS)', 
            #                f"{self.foh_data['total_net_revenue']:.2f}",
            #                f"{self.awards_data['total_net_revenue']:.2f}",
            #                f"{self.total_net_revenue:.2f}"])
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
        foh_revenue, foh_net_revenue = self.calculate_foh_financials()
        awards_revenue, awards_net_revenue = self.calculate_awards_financials()
        self.total_revenue = foh_revenue + awards_revenue
        self.total_net_revenue = foh_net_revenue + awards_net_revenue
        
        print("\n" + "=" * 70)
        print("💎 OVERALL FINANCIAL SUMMARY")
        print("=" * 70)
        
        total_votes = self.foh_data['total_votes'] + self.awards_data['total_votes']
        total_transactions = self.foh_data['total_transactions'] + self.awards_data['total_transactions']
        
        print(f"🏆 Grand Total Gross Revenue: GH₵ {self.total_revenue:,.2f}")
        # print(f"💎 Grand Total Net Revenue: GH₵ {self.total_net_revenue:,.2f} (after {self.fee_percentage}% fees)")
        # print(f"💸 Total Fees Deducted: GH₵ {self.total_revenue - self.total_net_revenue:,.2f}")
        print(f"🗳️  Grand Total Votes: {total_votes:,}")
        print(f"📊 Grand Total Transactions: {total_transactions:,}")
        
        if self.total_revenue > 0:
            foh_percentage = (foh_revenue / self.total_revenue) * 100
            awards_percentage = (awards_revenue / self.total_revenue) * 100
            
            print(f"\n📈 Gross Revenue Split:")
            print(f"   FOH (Ideal CEO): GH₵ {foh_revenue:,.2f} ({foh_percentage:.1f}%)")
            print(f"   Awards: GH₵ {awards_revenue:,.2f} ({awards_percentage:.1f}%)")
            
            # print(f"\n💎 Net Revenue Split:")
            # print(f"   FOH (Ideal CEO): GH₵ {foh_net_revenue:,.2f}")
            # print(f"   Awards: GH₵ {awards_net_revenue:,.2f}")
        
        avg_transaction = self.total_revenue / total_transactions if total_transactions > 0 else 0
        print(f"\n💳 Average Transaction: GH₵ {avg_transaction:.2f}")
        
        # Performance metrics
        if total_votes > 0:
            print(f"\n🎯 Performance Metrics:")
            print(f"   Vote-to-Revenue Ratio: 1 vote = GH₵ {self.total_revenue / total_votes:.2f}")
            print(f"   Transaction Efficiency: {total_votes / total_transactions:.1f} votes per transaction")
            # print(f"   Fee Impact: {((self.total_revenue - self.total_net_revenue) / self.total_revenue * 100):.1f}% of revenue goes to fees")

def main():
    parser = argparse.ArgumentParser(description='Enhanced HESA Financial Monitor')
    parser.add_argument('--detailed', action='store_true', help='Show detailed breakdown')
    parser.add_argument('--export', action='store_true', help='Export data to CSV files')
    args = parser.parse_args()
    
    print("💰 ENHANCED HESA FINANCIAL MONITORING SYSTEM")
    print("=" * 70)
    print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create Flask app context
    app = create_app()
    with app.app_context():
        monitor = EnhancedFinancialMonitor()
        
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
        
        # if not args.detailed:
        #     print("💡 Tip: Use --detailed for complete breakdown")
        # if not args.export:
        #     print("💡 Tip: Use --export to save data to CSV files")

if __name__ == "__main__":
    main()