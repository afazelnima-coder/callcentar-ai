from schemas.output_schemas import QualityScores, RubricScore


def calculate_overall_grade(percentage: float) -> str:
    """Convert percentage score to letter grade."""
    if percentage >= 90:
        return "A"
    elif percentage >= 80:
        return "B"
    elif percentage >= 70:
        return "C"
    elif percentage >= 60:
        return "D"
    else:
        return "F"


def calculate_total_score(scores: QualityScores) -> tuple[int, float]:
    """Calculate total points and percentage from all rubric items."""
    total = 0

    # Sum all category scores
    for category in [
        scores.greeting,
        scores.communication,
        scores.resolution,
        scores.professionalism,
        scores.closing,
    ]:
        for field_name, field_value in category:
            if isinstance(field_value, RubricScore):
                total += field_value.score

    percentage = (total / 95) * 100  # 19 items x 5 max = 95
    return total, percentage
