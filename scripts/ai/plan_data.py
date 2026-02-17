"""
Shared training plan data for the 2026 Spring HM Sub-2:00 Campaign.

Single source of truth — imported by both the Compliance dashboard page
and the AI metrics engine.
"""

from datetime import datetime


CAMPAIGN_START = datetime(2026, 1, 5)

WEEKLY_PLAN = {
    1: {"phase": "Recovery", "volume_km": 19, "strength": 2, "key_workout": "Easy runs only"},
    2: {"phase": "Recovery", "volume_km": 28, "strength": 2, "key_workout": "Fartlek reintroduction"},
    3: {"phase": "Base", "volume_km": 35, "strength": 2, "key_workout": "First tempo (4km@5:55)"},
    4: {"phase": "Base (Deload)", "volume_km": 30, "strength": 2, "key_workout": "Strides only"},
    5: {"phase": "Base", "volume_km": 37, "strength": 2, "key_workout": "Tempo 5km@5:50"},
    6: {"phase": "Base", "volume_km": 39, "strength": 2, "key_workout": "First intervals (5x1km@5:40)"},
    7: {"phase": "Base", "volume_km": 42, "strength": 2, "key_workout": "Tempo 6km@5:45"},
    8: {"phase": "Base (Deload)", "volume_km": 31, "strength": 2, "key_workout": "Strides only"},
    9: {"phase": "Build", "volume_km": 41, "strength": 2, "key_workout": "Intervals 6x1km@5:35"},
    10: {"phase": "Build", "volume_km": 43, "strength": 2, "key_workout": "Tempo 6km@5:40"},
    11: {"phase": "Build", "volume_km": 42, "strength": 2, "key_workout": "VO2max 5x800m@5:15-5:25"},
    12: {"phase": "Build", "volume_km": 40, "strength": 2, "key_workout": "Progressive threshold"},
    13: {"phase": "10K Taper", "volume_km": 27, "strength": 2, "key_workout": "Sharpener 4x600m@5:15"},
    14: {"phase": "10K RACE", "volume_km": 24, "strength": 1, "key_workout": "Race: Target 52:00-54:00"},
    15: {"phase": "Specific", "volume_km": 25, "strength": 2, "key_workout": "Recovery week"},
    16: {"phase": "Specific", "volume_km": 40, "strength": 2, "key_workout": "Long run 8km@5:50 (HM pace)"},
    17: {"phase": "Specific", "volume_km": 44, "strength": 2, "key_workout": "Long run 10km@5:45-5:50 (KEY)"},
    18: {"phase": "Specific", "volume_km": 38, "strength": 2, "key_workout": "HM rehearsal 5km@5:40"},
    19: {"phase": "Taper", "volume_km": 28, "strength": 1, "key_workout": "Sharpener 3x1km@5:35"},
    20: {"phase": "HM RACE", "volume_km": 35, "strength": 0, "key_workout": "Race: Target 2:00-2:03"},
}

PHASE_PACES = {
    "Recovery": {"easy": (435, 465), "tempo": None, "interval": None},
    "Base": {"easy": (420, 450), "tempo": (350, 360), "interval": (330, 345)},
    "Build": {"easy": (405, 435), "tempo": (340, 350), "interval": (320, 335)},
    "Specific": {"easy": (405, 435), "tempo": (335, 345), "interval": (315, 330)},
    "Taper": {"easy": (405, 435), "tempo": (335, 345), "interval": (315, 330)},
}

KEY_DATES = {
    "10K Race": datetime(2026, 4, 12),
    "HM Race": datetime(2026, 5, 24),
    "Goal Review": datetime(2026, 2, 22),
}

# Risk months with historical violation rates
HIGH_RISK_MONTHS = {2: 46.2, 4: 38.5, 5: 27.8}
MEDIUM_RISK_MONTHS = {1: 31.2, 3: 25.0, 6: 20.0}

FLOOR_THRESHOLD_KM = 15
ELEVATED_FLOOR_KM = 20

# Runner profile — used for biomechanics targets
RUNNER_HEIGHT_CM = 188
RUNNER_WEIGHT_KG = 80
RUNNER_BMI = round(RUNNER_WEIGHT_KG / (RUNNER_HEIGHT_CM / 100) ** 2, 1)  # ~22.6

# Stride length targets by effort (% of height, research-based for 188cm)
# Easy: 48-53% of height, Tempo: 53-58%, Interval: 58-63%
STRIDE_TARGETS = {
    "easy":     {"min_cm": round(RUNNER_HEIGHT_CM * 0.48), "max_cm": round(RUNNER_HEIGHT_CM * 0.53)},   # 90-100cm
    "tempo":    {"min_cm": round(RUNNER_HEIGHT_CM * 0.53), "max_cm": round(RUNNER_HEIGHT_CM * 0.58)},   # 100-109cm
    "interval": {"min_cm": round(RUNNER_HEIGHT_CM * 0.58), "max_cm": round(RUNNER_HEIGHT_CM * 0.63)},   # 109-118cm
}

# Cadence targets by effort (spm, for 188cm/80kg recreational HM runner)
CADENCE_TARGETS = {
    "easy":     {"min": 160, "max": 170},
    "tempo":    {"min": 170, "max": 180},
    "interval": {"min": 175, "max": 190},
}

# HR drift targets by effort (% first-to-last quarter)
# Negative splits naturally inflate HR drift, so flag with context
HR_DRIFT_TARGETS = {
    "easy":     {"ideal": 5.0, "acceptable": 7.0, "concern": 12.0},
    "tempo":    {"ideal": 8.0, "acceptable": 10.0, "concern": 15.0},
    "interval": {"ideal": 8.0, "acceptable": 10.0, "concern": 15.0},
    "long":     {"ideal": 10.0, "acceptable": 12.0, "concern": 15.0},
}


def get_campaign_week(date: datetime) -> int:
    """Calculate which campaign week a date falls in (1-20). Returns 0 if before campaign."""
    days_since_start = (date - CAMPAIGN_START).days
    if days_since_start < 0:
        return 0
    week = (days_since_start // 7) + 1
    return min(week, 20)


def get_phase_for_week(week_num: int) -> str:
    """Get phase name for a given week number."""
    if week_num in WEEKLY_PLAN:
        return WEEKLY_PLAN[week_num]["phase"]
    return "Unknown"


def get_target_volume(week_num: int) -> float:
    """Get target volume in km for a given week."""
    if week_num in WEEKLY_PLAN:
        return WEEKLY_PLAN[week_num]["volume_km"]
    return 0.0


def get_key_workout(week_num: int) -> str:
    """Get key workout description for a given week."""
    if week_num in WEEKLY_PLAN:
        return WEEKLY_PLAN[week_num]["key_workout"]
    return ""


def is_high_risk_month(month: int) -> bool:
    return month in HIGH_RISK_MONTHS


def get_month_risk_rate(month: int) -> float:
    """Get historical violation rate for a month. Returns 0 if not a risk month."""
    return HIGH_RISK_MONTHS.get(month, MEDIUM_RISK_MONTHS.get(month, 0.0))
