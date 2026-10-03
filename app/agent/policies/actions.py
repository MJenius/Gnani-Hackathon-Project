CLASSES = {'contact.notify_delay': 'B', 'payment.purchase': 'C'}

def validate(tool, authorized=False, confirmed=False):
    action_class = CLASSES.get(tool)
    if action_class is None:
        raise PermissionError('Unknown tool blocked')
    if action_class == 'B' and not authorized:
        raise PermissionError('Notification authorization required')
    if action_class == 'C' and not (authorized and confirmed):
        raise PermissionError('Explicit action confirmation required')
    return action_class
