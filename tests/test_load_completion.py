from __future__ import annotations

from pace.domain.models import WeekLoad
from pace.domain.rules.completion import check as c_check
from pace.domain.rules.completion import streak
from pace.domain.rules.load import check as l_check


def test_growth_within_ten_percent_ok():
    assert l_check([40.0, 44.0]) == []


def test_growth_over_ten_percent_flagged():
    findings = l_check([40.0, 46.0])
    assert findings[0].rule_id == "load.increase"
    assert "15%" in findings[0].message


def test_zero_prev_skipped():
    assert l_check([0.0, 30.0]) == []


def test_single_low_week_not_enough():
    assert streak([WeekLoad(1, 40, 38), WeekLoad(2, 46, 18)]) == []


def test_two_consecutive_low_weeks():
    weeks = [WeekLoad(1, 40, 38), WeekLoad(2, 46, 18), WeekLoad(3, 50, 28)]
    assert streak(weeks) == [2, 3]


def test_completion_finding_rule_id():
    weeks = [WeekLoad(1, 40, 38), WeekLoad(2, 46, 18), WeekLoad(3, 50, 28)]
    findings = c_check(weeks)
    assert findings[0].rule_id == "plan.replan"


def test_non_consecutive_lows_no_finding():
    weeks = [WeekLoad(1, 40, 18), WeekLoad(2, 46, 46), WeekLoad(3, 50, 20)]
    assert c_check(weeks) == []
