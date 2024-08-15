DAYS = ['mon', 'tue', 'wed', 'thr', 'fri', 'sat', 'sun']
SHIFTS = ['9', '14', '18']
SHIFT_TYPES = ["cut", "glu", "san", "che", "vab", "lam", "cor"]

def get_shift_index(shift):
    d,s = shift.split("_")
    return DAYS.index(d) * 3 + SHIFTS.index(s)
    