from flask import Flask, render_template, request, jsonify
from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime
import time
import threading
import schedule
import json
import os
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-key-for-development')
# Database (using JSON files for now instead of a paid database service)
class DataStore:
    def __init__(self):
        self.nfl_data = {}
        self.nba_data = {}
        self.last_updated = {
            'nfl': None,
            'nba': None
        }
        
        # Load existing data if available
        try:
            with open('data/nfl_data.json', 'r') as f:
                self.nfl_data = json.load(f)
            with open('data/nba_data.json', 'r') as f:
                self.nba_data = json.load(f)
        except FileNotFoundError:
            pass

    def save_data(self):
        # Save data to JSON files
        with open('data/nfl_data.json', 'w') as f:
            json.dump(self.nfl_data, f)
        with open('data/nba_data.json', 'w') as f:
            json.dump(self.nba_data, f)

data_store = DataStore()

class StatsScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def scrape_nfl_stats(self):
        try:
            # Example: Scraping from Pro Football Reference
            # We'll scrape player stats from their game logs
            base_url = "https://www.pro-football-reference.com/years/2023/rushing.htm"
            response = requests.get(base_url, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the stats table
            stats_table = soup.find('table', {'id': 'rushing'})
            if stats_table:
                for row in stats_table.find_all('tr')[1:]:  # Skip header row
                    cols = row.find_all('td')
                    if cols:
                        player_name = cols[0].text.strip()
                        team = cols[1].text.strip()
                        stats = {
                            'rushing_yards': cols[4].text.strip(),
                            'touchdowns': cols[7].text.strip(),
                            'yards_per_game': cols[9].text.strip(),
                            'games_played': cols[2].text.strip()
                        }
                        data_store.nfl_data[player_name] = {
                            'team': team,
                            'stats': stats,
                            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
            
            data_store.save_data()
            data_store.last_updated['nfl'] = datetime.now()
            print("NFL stats updated successfully")
            
        except Exception as e:
            print(f"Error updating NFL stats: {e}")

    def scrape_nba_stats(self):
        try:
            # Example: Scraping from Basketball Reference
            base_url = "https://www.basketball-reference.com/leagues/NBA_2024_per_game.html"
            response = requests.get(base_url, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            stats_table = soup.find('table', {'id': 'per_game_stats'})
            if stats_table:
                for row in stats_table.find_all('tr')[1:]:
                    cols = row.find_all('td')
                    if cols:
                        player_name = row.find('a').text.strip()
                        team = cols[3].text.strip()
                        stats = {
                            'points_per_game': cols[28].text.strip(),
                            'rebounds': cols[22].text.strip(),
                            'assists': cols[23].text.strip(),
                            'games_played': cols[4].text.strip()
                        }
                        data_store.nba_data[player_name] = {
                            'team': team,
                            'stats': stats,
                            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
            
            data_store.save_data()
            data_store.last_updated['nba'] = datetime.now()
            print("NBA stats updated successfully")
            
        except Exception as e:
            print(f"Error updating NBA stats: {e}")

# Initialize scraper
stats_scraper = StatsScraper()

# Set up automatic updates
def start_scraper():
    schedule.every(6).hours.do(stats_scraper.scrape_nfl_stats)
    schedule.every(6).hours.do(stats_scraper.scrape_nba_stats)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# Start scraper in background thread
scraper_thread = threading.Thread(target=start_scraper)
scraper_thread.daemon = True
scraper_thread.start()

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/search', methods=['POST'])
def search():
    sport = request.form.get('sport', '').lower()
    query = request.form.get('query', '').strip()
    
    results = {}
    
    if sport == 'nfl':
        data = data_store.nfl_data
    elif sport == 'nba':
        data = data_store.nba_data
    else:
        return jsonify({"error": "Invalid sport selected"})
    
    # Parse the query
    for player_name, player_data in data.items():
        if query.lower() in player_name.lower():
            results[player_name] = player_data
    
    return jsonify(results)

@app.route('/api/query', methods=['POST'])
def query_stats():
    sport = request.json.get('sport', '').lower()
    player = request.json.get('player', '').strip()
    stat_type = request.json.get('stat_type', '').strip()
    threshold = float(request.json.get('threshold', 0))
    
    if sport == 'nfl':
        data = data_store.nfl_data
    elif sport == 'nba':
        data = data_store.nba_data
    else:
        return jsonify({"error": "Invalid sport selected"})
    
    if player not in data:
        return jsonify({"error": "Player not found"})
    
    player_data = data[player]
    if stat_type not in player_data['stats']:
        return jsonify({"error": "Stat type not found"})
    
    stat_value = float(player_data['stats'][stat_type])
    games_played = int(player_data['stats']['games_played'])
    
    response = {
        "player": player,
        "stat_type": stat_type,
        "threshold": threshold,
        "current_value": stat_value,
        "games_played": games_played,
        "last_updated": player_data['last_updated']
    }
    
    return jsonify(response)

if __name__ == '__main__':
    # Initial scrape
    stats_scraper.scrape_nfl_stats()
    stats_scraper.scrape_nba_stats()
    
    app.run(debug=True)

    # Add this with your other imports at the top if not already there
from flask import session

# Add this new route before if __name__ == '__main__':
@app.route('/api/connect-wallet', methods=['POST'])
def connect_wallet():
    data = request.json
    wallet_address = data.get('wallet_address')
    
    if not wallet_address:
        return jsonify({'error': 'No wallet address provided'}), 400
    
    # If user is logged in, update their wallet address
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        user.solana_wallet = wallet_address
        db.session.commit()
    
    # Store wallet address in session
    session['wallet_address'] = wallet_address
    
    return jsonify({'success': True})

# Leave your existing if __name__ == '__main__': block at the bottom
