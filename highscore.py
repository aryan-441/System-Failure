'''Locally saved highscore through json'''
import json
from pathlib import Path

filepath = Path(__file__).parent / 'highscore.json'

def load_high_score():
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            score = data.get('high_score',0)

            if type(score) == int and score >= 0:
                return score
    except (FileNotFoundError, OSError, ValueError, TypeError):
        pass
    return 0
def get_high_score(score):
    with open(filepath, 'w') as f:
        json.dump({'high_score' : score}, f, indent=4)
