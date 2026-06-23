from .clinicaltrials import fetch_trials

def extract() -> list[dict]:
    return fetch_trials("diabetes", max_results=8)
