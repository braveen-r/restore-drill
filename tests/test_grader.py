from drill.scoring.grader import RecoveryGrader


def test_perfect_grade_a():
    # Fast restore and fresh snapshot with all checks passing should score 100 (Grade A)
    grader = RecoveryGrader(max_rto_seconds=60.0, max_rpo_hours=24.0)
    result = grader.calculate_grade(
        rto_seconds=12.5,
        rpo_hours=4.0,
        critical_checks={"db_file": True, "config": True},
        smoke_status="PASS",
    )
    assert result["score"] == 100
    assert result["grade"] == "A"
    assert result["penalties"] == []


def test_missing_critical_check_and_smoke_failure():
    # Missing 1 critical check (-35) and failed smoke test (-25) -> 40 (Grade F)
    grader = RecoveryGrader(max_rto_seconds=60.0, max_rpo_hours=24.0)
    result = grader.calculate_grade(
        rto_seconds=20.0,
        rpo_hours=6.0,
        critical_checks={"db_file": False, "config": True},
        smoke_status="FAIL",
    )
    assert result["score"] == 40
    assert result["grade"] == "F"
    assert len(result["penalties"]) == 2


def test_rto_and_rpo_threshold_penalties():
    # RTO > 2x max_rto (-20) and RPO > 72h (-25) -> 55 (Grade F)
    grader = RecoveryGrader(max_rto_seconds=30.0, max_rpo_hours=24.0)
    result = grader.calculate_grade(
        rto_seconds=75.0,
        rpo_hours=80.0,
        critical_checks={"db_file": True},
        smoke_status="PASS",
    )
    assert result["score"] == 55
    assert result["grade"] == "F"


def test_score_clamped_at_zero():
    # Severe violations should never produce a negative score
    grader = RecoveryGrader(max_rto_seconds=10.0, max_rpo_hours=12.0)
    result = grader.calculate_grade(
        rto_seconds=999.0,
        rpo_hours=200.0,
        critical_checks={"a": False, "b": False, "c": False, "d": False},
        smoke_status="FAIL",
    )
    assert result["score"] == 0
    assert result["grade"] == "F"
