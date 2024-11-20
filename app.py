from flask import Flask, render_template, request, jsonify
app = Flask(__name__)

# Sample data structure for demonstration
sample_data = {
    "nfl": {
        "players": {
            "Tom Brady": {"team": "Retired", "stats": {"passing_yards": 89214, "touchdowns": 649}},
            "Patrick Mahomes": {"team": "Chiefs", "stats": {"passing_yards": 24241, "touchdowns": 192}}
        },
        "teams": {
            "Chiefs": {"wins": 14, "losses": 3},
            "Eagles": {"wins": 11, "losses": 6}
        }
    },
    "nba": {
        "players": {
            "LeBron James": {"team": "Lakers", "stats": {"points": 38652, "assists": 10420}},
            "Stephen Curry": {"team": "Warriors", "stats": {"points": 22774, "assists": 5740}}
        },
        "teams": {
            "Lakers": {"wins": 47, "losses": 35},
            "Warriors": {"wins": 44, "losses": 38}
        }
    }
}

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/search', methods=['POST'])
def search():
    sport = request.form.get('sport', '').lower()
    search_term = request.form.get('team_player', '').strip()
    line = request.form.get('line', '')
    location = request.form.get('location', '')
    
    results = {}
    
    if sport in sample_data:
        # Search in players
        if search_term:
            for player, data in sample_data[sport]['players'].items():
                if search_term.lower() in player.lower():
                    results[player] = data
        
        # Search in teams
        for team, data in sample_data[sport]['teams'].items():
            if search_term.lower() in team.lower():
                results[team] = data
    
    return render_template('home.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)
    