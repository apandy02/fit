from datetime import datetime, timedelta


def get_current_week_dates():
    """Get a list of dates for the current week (Sunday through Saturday)
    
    Returns:
        list[datetime.date]: List of 7 dates starting with Sunday of current week
    """
    today = datetime.today()
    days_since_sunday = today.weekday() + 1
    if days_since_sunday == 7:
        days_since_sunday = 0
        
    sunday = today - timedelta(days=days_since_sunday)
    
    week_dates = []
    for i in range(7):
        date = sunday + timedelta(days=i)
        week_dates.append(date.date())
        
    return week_dates
