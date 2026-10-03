def notify_delay(connection, mission_id, inputs):
    connection.execute('INSERT INTO notifications VALUES (?, ?, ?)',
                       (mission_id, inputs['contact'], inputs['delay_minutes']))
    return {'simulated': True, 'delivered': True, **inputs}
