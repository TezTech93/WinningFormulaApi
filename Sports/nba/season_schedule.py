import datetime as dt

now = dt.datetime.now()
today = dt.datetime.date(now.year,now.month,now.day)

last_season_end_date = ''

summer_league = ''
pre_season = ''
cur_reg_season = ''
all_star_break = ''
playoffs = ''

next_season_start = ''

def get_current_season_status():
    if today >= cur_reg_season[0] and today <= cur_reg_season[1]:
        cur_season = 'Regular Season'
    elif today >= summer_league[0] and today <= summer_league[1]:
        cur_season = 'Summer League'
    elif today >= pre_season[0] and today <= pre_season[1]:
        cur_season = 'Pre-Sesason'
    elif today >= playoffs[0] and today <= playoffs[1]:
        cur_season = 'Playoffs'
    return cur_season