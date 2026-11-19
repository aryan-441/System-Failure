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
        if isinstance(data,dict):
            for difficulty in scores:
                score = data.get(difficulty,0)

                if type(score) is int and score >= 0:
                    scores[difficulty] = score
    except (FileNotFoundError, OSError, ValueError, TypeError):
        pass
    return scores
def get_high_score(score, difficulty):
    scores = load_high_score()
    if difficulty not in scores:
        raise ValueError("Invalid difficulty.")
    if type(score) is not int or score <0:
        raise ValueError("Invalid scroe.")

    scores[difficulty] = max(scores[difficulty], score)
    with open(filepath,'w') as f:
        json.dump(scores,f,indent=4)
