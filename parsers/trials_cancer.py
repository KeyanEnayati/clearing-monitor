from .clinicaltrials import fetch_trials

def extract() -> list[dict]:
    return fetch_trials("cancer", max_results=8)
