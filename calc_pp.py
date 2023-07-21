import osu_diff_calc as odc
from osu import Client, GameModeStr, Beatmapset, BeatmapsetSearchFilter, GameModeInt, Mods

def init_api():
    global api
    api = Client.from_client_credentials(20810, "tNVBdaVDZL3naL2fZDUFrRQOwhFo8aGgg9bLB0Es", None)
    return api

def calculate_pp(beatmap_attributes, beatmap, score_attributes):
    score = odc.OsuScoreAttributes()
    for k, v in score_attributes.items():
        setattr(score, k, v)
    calculator = odc.OsuPerformanceCalculator(odc.GameMode.STANDARD, odc.OsuDifficultyAttributes.from_attributes({
            'aim_difficulty': beatmap_attributes.mode_attributes.aim_difficulty,
            'speed_difficulty': beatmap_attributes.mode_attributes.speed_difficulty,
            'flashlight_difficulty': beatmap_attributes.mode_attributes.flashlight_difficulty,
            'slider_factor': beatmap_attributes.mode_attributes.slider_factor,
            'speed_note_count': beatmap_attributes.mode_attributes.speed_note_count,
            'approach_rate': beatmap_attributes.mode_attributes.approach_rate,
            'overall_difficulty': beatmap_attributes.mode_attributes.overall_difficulty,
            'max_combo': beatmap_attributes.max_combo,
            'drain_rate': beatmap.drain,
            'hit_circle_count': beatmap.count_circles,
            'slider_count': beatmap.count_sliders,
            'spinner_count': beatmap.count_spinners}), score)
    calcpp = calculator.calculate()
    return calcpp
    
def pp(beatmap, beatmap_attributes, mods, accuracy):
    score_attributes = {'mods': mods, "accuracy":accuracy, "score_max_combo":beatmap_attributes.max_combo, "count_great":beatmap.count_circles+beatmap.count_sliders+beatmap.count_spinners, "count_ok":0, "count_meh":0, "count_miss":0}
    return calculate_pp(beatmap_attributes, beatmap, score_attributes)




