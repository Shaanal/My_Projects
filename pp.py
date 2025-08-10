GRADE_POINTS = {
    'A+': 10, 'A': 10, 'A-': 9,
    'B+': 8, 'B': 7, 'C': 6,
    'D': 5, 'F': 0
}

def calculate_sgpa(subjects):
    total_points = 0
    total_credits = 0
    for subject in subjects:
        grade_point = GRADE_POINTS.get(subject['grade'].upper(), 0)
        credit = subject['credit']
        total_points += grade_point * credit
        total_credits += credit
    return round(total_points / total_credits, 2) if total_credits != 0 else 0

def calculate_cgpa(prev_total_credits, prev_cgpa, curr_credits, curr_sgpa):
    total_credits = prev_total_credits + curr_credits
    weighted_sum = (prev_cgpa * prev_total_credits) + (curr_sgpa * curr_credits)
    return round(weighted_sum / total_credits, 2) if total_credits != 0 else 0

def calculate_needed_sgpa(prev_total_credits, prev_cgpa, curr_credits, needed_cgpa):
    total_credits = prev_total_credits + curr_credits
    curr_sgpa = ((needed_cgpa * total_credits) - (prev_cgpa * prev_total_credits))/ curr_credits

    return round(curr_sgpa, 2) if curr_credits != 0 else 0

def estimate_course_grade(components, weights):
    total = 0
    for comp, score in components.items():
        weight = weights.get(comp, 0)
        total += score * (weight / 100)
    return round(total, 2)
