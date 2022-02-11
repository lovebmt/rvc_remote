# labpc/consumers.py
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import Board


class messageClientConsumer(WebsocketConsumer):
    """Websocket consumer for message client.

    Attributes:
        user_count: number of request for users.
        handle: request ID from user.

    """

    def connect(self):
        """Handling connect request."""
        # if not self.scope["user"].id:
            # self.close()
        self.user = self.scope["user"]
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = "labpc_%s" % self.room_name

        print("%s connected" % str(self.user.username))

        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
        self.accept()
        self.send( #send in socket
            text_data=json.dumps(
                {
                    "from": "server",
                    "to": "user",
                    "message": "connect success",
                    "evt": "connect",
                }
            )
        )
    def disconnect(self, close_code):
        """Handling disconnect request."""
        async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)

    def receive(self, text_data):
        """Receive message from WebSocket.

        Args:
            text_data: Receive data.

        """
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get("message",None)
            mfrom = text_data_json.get("from",None)
            to = text_data_json.get("to","all")
            evt = text_data_json.get("evt",None)

            print("[{0}->{1}:{2}] {3}\n".format(mfrom,to,evt,str(message)))
            if evt == "connect":
                return ""
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    "type": "room_message",
                    "from": mfrom,
                    "to" : to,
                    "message": message,
                    "evt":evt
                }
            )

        except ValueError:
            return ""

    def room_message(self, event):
        """Receive message from lab PC.

        Args:
            event: event message.

        """
        self.send( #send in socket
            text_data=json.dumps(
                {
                    "from": event["from"],
                    "to": event["to"],
                    "evt":event["evt"],
                    "message": event["message"]
                }
            )
        )
            