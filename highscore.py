'''Locally saved highscore through json'''
import json
from pathlib import Path

filepath = Path(__file__).parent / 'highscore.json'

def load_high_score():
    scores = {
        'easy':0,
        'medium':0,
        'hard':0,
    }
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        for difficulty in scores:
            score = data.get(difficulty, 0)
            if type(score) == int and score >= 0:
                scores[difficulty] = max(scores[difficulty],score)
    except (FileNotFoundError, OSError, ValueError, TypeError):
        pass
    return 0
def get_high_score(score):
    with open(filepath, 'w') as f:
        json.dump({'high_score' : score}, f, indent=4)