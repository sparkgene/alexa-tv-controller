# -*- coding: utf-8 -*-

import json
from uuid import uuid4
import time
import random
import boto3

THING_NAME = "tv-controller"
TV_ON = "tv_on"
TV_OFF = "tv_off"
iot_client = boto3.client('iot-data', region_name='ap-northeast-1')


# ユニークなUUIDを生成
def unique_id():
    return str(uuid4())

# APIの日付形式に合わせたGMTを返す
def utc_timestamp():
    return time.strftime("%Y-%m-%dT%H:%M:%S.00Z", time.gmtime())

def lambda_handler(event, context):
    print(json.dumps(event))
    header = event["directive"]["header"]

    if header["namespace"] == "Alexa.Discovery":
        return alexa_discover(header, event["directive"]["payload"])
    elif header["namespace"] == "Alexa.PowerController":
        return power_control(header, event["directive"]["endpoint"])
    elif header["namespace"] == "Alexa" and header["name"] == "ReportState":
        return report_status(header, event["directive"]["endpoint"])

    # 例外パターンはサンプルに含めてません
    print('un supported request')
    return None

# 現在のステータスをレポート
def report_status(header, endpoint):
    command = describe_current_command
    if command == TV_ON:
      status = "ON"
    else:
      status = "OFF"

    return power_control_response(header, endpoint, status)

def alexa_discover(header, payload):

    if header["name"] == "Discover":
        return discover_device(header, payload)
    
    # ホントはちゃんと返さないとダメ
    return None

def discover_device(header, payload):

    # TVだけなので、固定のエンドポイント
    endpoints = [
      {
          "endpointId": "my-living-tv",
          "manufacturerName": "sparkgene corp",
          "friendlyName": "リビングのテレビ",
          "description": "テレビの電源を操作できます",
          "displayCategories": [
              "TV"
          ],
          "capabilities": [
              {
                  "type": "AlexaInterface",
                  "interface": "Alexa.PowerController",
                  "version": "3",
                  "properties": {
                      "supported": [
                      {
                          "name": "powerState"
                      }
                      ],
                      "proactivelyReported": False,
                      "retrievable": True
                  }
              }    
          ]
      }
    ]

    return build_discover_response(header, endpoints)

# discover用のレスポンスを返す
def build_discover_response(header, endpoints):
    response = {
        "event": {
            "header": {
                "namespace": "Alexa.Discovery",
                "name": "Discover.Response",
                "payloadVersion": "3",
                "messageId": unique_id()
            },
            "payload": {
                "endpoints": endpoints
            }
        }
    }

    print(json.dumps(response))
    return response

# 電源の操作
def power_control(header, endpoint):
    print('power_control')
    print("{} endpointId: {}".format(header["name"], endpoint["endpointId"]))

    if header["name"] == "TurnOn":
        send_command(TV_ON)
        return power_control_response(header, endpoint, "ON")
    else:
        send_command(TV_OFF)
        return power_control_response(header, endpoint, "OFF")

# 電源の操作結果を返す
def power_control_response(header, endpoint, value):
    name = "Response"
    if header["namespace"] == "Alexa" and header["name"] == "ReportState":
        name = "StateReport"

    response = {
        "context": {
            "properties": [ {
            "namespace": "Alexa.PowerController",
            "name": "powerState",
            "value": value,
            "timeOfSample": utc_timestamp(),
            "uncertaintyInMilliseconds": 500
            } ]
        },
        "event": {
            "header": {
            "namespace": "Alexa",
            "name": name,
            "payloadVersion": "3",
            "messageId": header["messageId"],
            "correlationToken": header["correlationToken"]
            },
            "endpoint": {
                "scope": {
                    "type": "BearerToken",
                    "token": endpoint["scope"]["token"]
                },
                "endpointId": endpoint["endpointId"]
            },
            "payload": {}
        }
    }

    print(json.dumps(response))
    return response

# AWS IoT Shadow

# shadowの更新を行う
def send_command(command):
    shadow = {
        'state': {
            'desired': {
                'command': command,
                'counter': int(time.time())
            }
        }
    }
    payload = json.dumps(shadow)

    response = iot_client.update_thing_shadow(
        thingName=THING_NAME,
        payload= payload
    )
    return True

# shadowの現在の状態を取得
def describe_current_command():
    response = iot_client.get_thing_shadow(
        thingName=THING_NAME
    )
    streamingBody = response["payload"]
    jsonState = json.loads(streamingBody.read())
    print(jsonState)
    return jsonState['state']['desired']['command']