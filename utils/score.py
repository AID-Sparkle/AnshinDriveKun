def calculate_risk_score(time, age, weather, vehicle):
    TIME_SCORE = {
        "早朝(4:00~7:00)": 4,
        "午前(7:00~12:00)": 2,
        "午後(12:00~16:00)": 1,
        "夕方(16:00~18:00)": 3,
        "夜(18:00~22:00)": 4,
        "深夜(22:00~4:00)": 5
    }

    WEATHER_SCORE = {
        "晴れ": 1,
        "曇り": 2,
        "雨": 3,
        "雷": 4,
        "濃霧": 5,
        "雪": 5
    }

    AGE_SCORE = {
        "18~24歳": 3,
        "25~34歳": 1,
        "35~44歳": 1,
        "45~54歳": 3,
        "65~74歳": 4,
        "75歳以上": 5
    }

    VEHICLE_SCORE = {
        "乗用車": 1,
        "貨物車": 2,
        "バイク": 5,
        "自転車": 3
    }

    score = 0
    score += TIME_SCORE.get(time, 0)
    score += AGE_SCORE.get(age, 0)
    score += WEATHER_SCORE.get(weather, 0)
    score += VEHICLE_SCORE.get(vehicle, 0)
    return score
