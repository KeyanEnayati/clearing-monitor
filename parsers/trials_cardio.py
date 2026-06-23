from .clinicaltrials import fetch_trials

def extract() -> list[dict]:
    return fetch_trials("cardiovascular disease", max_results=8)
