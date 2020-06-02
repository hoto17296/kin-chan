def activate(active: bool, t_begin: str, t_end: str) -> dict:
    active_option = {
      "value": "active",
      "text": {
        "type": "plain_text",
        "text": "リマインド通知を有効にする"
      }
    }
    view = {
      "type": "modal",
      "title": {
        "type": "plain_text",
        "text": "King of Time Reminder",
        "emoji": True
      },
      "blocks": [
        {
          "type": "section",
          "text": {
            "type": "plain_text",
            "text": "設定した時刻に出退勤していなかった場合にリマインド通知を送ることができます"
          },
          "accessory": {
            "type": "checkboxes",
            "action_id": "active",
            "options": [active_option],
          }
        },
        {
          "type": "section",
          "block_id": "t_begin",
          "text": {
            "type": "mrkdwn",
            "text": "出勤リマインド時刻"
          },
          "accessory": {
            "action_id": "t_begin",
            "type": "static_select",
            "placeholder": {
              "type": "plain_text",
              "text": "--:--",
            },
            "options": [
              {
                "text": {
                  "type": "plain_text",
                  "text": f'{h:02d}:{m:02d}'
                },
                "value": f'{h:02d}:{m:02d}'
              }
              for h in range(9, 13) for m in [0, 30]
            ],
            "initial_option": {
              "text": {
                "type": "plain_text",
                "text": t_begin,
              },
              "value": t_begin
            }
          }
        },
        {
          "type": "section",
          "block_id": "t_end",
          "text": {
            "type": "mrkdwn",
            "text": "退勤リマインド時刻"
          },
          "accessory": {
            "action_id": "t_end",
            "type": "static_select",
            "placeholder": {
              "type": "plain_text",
              "text": "--:--",
            },
            "options": [
              {
                "text": {
                  "type": "plain_text",
                  "text": f'{h:02d}:{m:02d}'
                },
                "value": f'{h:02d}:{m:02d}'
              }
              for h in range(18, 22) for m in [0, 30]
            ],
            "initial_option": {
              "text": {
                "type": "plain_text",
                "text": t_end,
              },
              "value": t_end,
            }
          }
        }
      ]
    }
    if active:
        view['blocks'][0]['accessory']['initial_options'] = [active_option]
    return view