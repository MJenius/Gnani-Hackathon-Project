CLASSES = {'contact.notify_delay': 'B', 'contact.negotiate':'B', 'calendar.reschedule':'B',
           'parking.select':'A', 'fuel.select':'A', 'payment.purchase': 'C'}

def validate(tool, authorized=False, confirmed=False):
    action_class = CLASSES.get(tool)
    if action_class is None:
        raise PermissionError('Unknown tool blocked')
    if action_class == 'B' and not authorized:
        raise PermissionError('Notification authorization required')
    if action_class == 'C' and not (authorized and confirmed):
        raise PermissionError('Explicit action confirmation required')
    return action_class

def validate_calendar_change(authorized, contact_result, proposed_time, confirmed=False):
    """External acceptance is a fact, not authorization for a different meeting time."""
    validate('calendar.reschedule',authorized)
    if contact_result.get('response')=='accepted' and contact_result.get('accepted_time')==proposed_time:
        return True
    if contact_result.get('response')=='rejected' and contact_result.get('counter_offer')==proposed_time:
        return confirmed
    raise PermissionError('Calendar change has no verified agreement')
