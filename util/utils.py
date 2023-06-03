import httpx


def get_body(result, fcm_token):
    results = [int(result[0][0]), int(result[1][0]), int(result[2][0])]
    message = ""
    if results[0] == 0:
        message += "Wrong head"
    if results[1] == 2:
        if message != "":
            message += ", "
        message += "Leaning back"
    elif result[1] == 3:
        if message != "":
            message += ", "
        message += "Leaning forward"
    if results[2] == 0:
        if message != "":
            message += ", "
        message += "Wrong leg"
    if message != "":
        return {
            "to": f"{fcm_token}",
            "priority": "high",
            "content_available": True,
            "notification": {
                "title": "Thông báo",
                "body": message
            },
            "data": {
                "content": {
                    "channelKey": "high_importance_channel",
                    "displayOnForeground": True,
                    "showWhen": True,
                    "autoDismissible": True,
                    "privacy": "Private",
                    "payload": {
                        "navigate": "true"
                    }
                },
                "actionButtons": [
                    {
                        "key": "notificaiton",
                        "label": "To notificaiton",
                        "actionType": "SilentAction"
                    }
                ],
                "Android": {
                    "content": {
                        "title": "Android! Notification",
                        "payload": {
                            "android": "android custom content!"
                        }
                    }
                },
                "iOS": {
                    "content": {
                        "title": "Jobs! The eagle has landed!",
                        "payload": {
                            "ios": "ios custom content!"
                        }
                    },
                    "actionButtons": [
                        {
                            "key": "REDIRECT",
                            "label": "Redirect message",
                            "autoDismissible": True
                        },
                        {
                            "key": "DISMISS",
                            "label": "Dismiss message",
                            "actionType": "DismissAction",
                            "isDangerousOption": True,
                            "autoDismissible": True
                        }
                    ]
                }
            }
        }
    else:
        return None
