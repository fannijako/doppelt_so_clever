SCORE_CATEGORIES = [
    (0, 140, "Half as clever."),
    (140, 160, "You can do better."),
    (160, 180, "On the right way."),
    (180, 200, "You should be happy!"),
    (200, 220, "You've been training!"),
    (220, 240, "Pretty, pretty clever!"),
    (240, 260, "People, look at this!"),
    (260, 280, "This can't be luck!"),
    (280, 300, "Respect!"),
    (300, 320, "Points = IQ!"),
    (320, None, "Twice as clever!"),
]


def get_score_rating(score: int) -> str:
    for lower, upper, label in SCORE_CATEGORIES:
        if upper is None:
            if score >= lower:
                return label
        elif lower <= score < upper:
            return label
    return ""
