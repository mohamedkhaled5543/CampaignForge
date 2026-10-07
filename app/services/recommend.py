GOAL_TO_DIRECTION = {
    "Awareness": ("lifestyle_focused", "Lifestyle content builds awareness by showing the product in the audience's daily life."),
    "Engagement": ("lifestyle_focused", "Relatable lifestyle content gets the audience reacting and sharing."),
    "Sales": ("conversion_focused", "Conversion-focused messaging puts the offer and the call to action first."),
    "Launch": ("product_focused", "A launch needs the audience to understand what the product is and does."),
}


def recommend_direction(goal):
    key, why = GOAL_TO_DIRECTION.get(goal, ("lifestyle_focused", ""))
    return {"key": key, "reason": why}
