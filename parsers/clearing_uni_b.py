from .clearing_simulation import get_courses

def extract() -> list[dict]:
    return get_courses("CLEARING_UNI_B")
