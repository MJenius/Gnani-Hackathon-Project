"""Named recovery checks reuse the unit assertions; no second test framework."""
import json
import unittest
from pathlib import Path

CHECKS={
    'duplicate_and_concurrent_commands_do_not_duplicate_actions':'duplicate request / stale revision',
    'stale_confirmation_and_denial':'stale confirmation',
    'parking_changes_during_execution_demo':'parking disappearance',
    'combined_failures_and_no_answer_are_bounded':'no answer / bounded retry',
    'rejected_time_replans_and_confirmation_gates_calendar':'rejected time',
    'failed_transition_preserves_committed_call_and_can_resume':'failed transition rollback',
    'service_failure_recovery_preserves_completed_history':'service failure / recovery',
    'user_change_keeps_completed_calendar_and_mission_id':'changed requirement',
    'malformed_plan_and_unsupported_goal_preserve_existing_mission':'malformed planner / unsupported goal',
    'late_route_escalates_without_repeating_calendar':'late arrival escalation',
    'repeated_conditions_and_requirements_are_noops':'repeated retry / mutation',
    'replan_explanation_is_persisted_and_resolved':'persisted explanation',
}

def main():
    discovered=unittest.defaultTestLoader.discover('tests',pattern='test_mission_v2.py')
    selected=unittest.TestSuite(test for suite in discovered for group in suite for test in group
                               if test._testMethodName.removeprefix('test_') in CHECKS)
    result=unittest.TextTestRunner(verbosity=1).run(selected)
    assert result.testsRun==len(CHECKS) and result.wasSuccessful()
    from app.evaluation.runners.restart_check import automatic
    automatic()
    output={'kind':'offline_chaos','checks_passed':result.testsRun+1,'checks_tested':len(CHECKS)+1,
            'checks':list(CHECKS.values())+['API process restart'],'providers_called':False}
    path=Path('data/chaos-results.json');path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(output,indent=2),encoding='utf-8');print(json.dumps(output,indent=2))

if __name__=='__main__': main()
