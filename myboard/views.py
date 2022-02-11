import random
import string
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import GetBoardsSerializer
from .models import Board, LABPC, CustomUser
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import SessionAuthentication
from django.core.exceptions import ObjectDoesNotExist

import requests
import json


def set_if_not_none(mapping, key, value):
    if value is not None:
        mapping[key] = value


def getStatusControl(control):
    control = control.lower()
    if control in ['on']:
        return Board.StatusPower.POWER_ON
    elif control in ['off']:
        return Board.StatusPower.POWER_OFF
    elif control in ["boot"]:
        return Board.StatusBoot.BOOT
    elif control in ["unboot"]:
        return Board.StatusBoot.UNBOOT


class GetShareBoardsAPI(APIView):
    """Get list of shared boards."""

    def get(self, request):
        print("Get list share board by ", end="")
        print(request.user)
        try:

            sort_board_id = request.GET.get('board_id', None)
            sort_using_by = request.GET.get('using_by', None)
            sort_labpc_id = request.GET.get('labpc_id', None)
            sort_pcd_ip = request.GET.get('pcd_ip', None)
            sort_board_type = request.GET.get('board_type', None)
            sort_board_lab_id = request.GET.get('board_lab_id', None)
            need_update_value = request.GET.get('update_value', True)
            # The params sort by
            sort_params = {}
            set_if_not_none(sort_params, 'id', sort_board_id)
            set_if_not_none(sort_params, 'usingBy', sort_using_by)
            set_if_not_none(sort_params, 'LABPCOwner__id', sort_labpc_id)
            set_if_not_none(sort_params, 'PCDOwner__ipaddr', sort_pcd_ip)
            set_if_not_none(sort_params, 'boardType', sort_board_type)
            set_if_not_none(sort_params, 'boardLabID', sort_board_lab_id)

            bs = Board.objects.filter(
                **sort_params,  isShareControl=True, isActivate=True)
            if need_update_value == True or need_update_value.lower() in ['true']:
                ls = []
                for b in bs:
                    if b.LABPCOwner.id in ls:
                        continue
                    url = "http://%s:%d/api/status/boards/?" % (
                        str(b.LABPCOwner.ipaddr), int(b.LABPCOwner.port))
                    try:
                        r = requests.get(url).json()
                    except:
                        r = {"ok": False}
                    if r.get("ok"):
                        ls.append(b.LABPCOwner.id)
                        rbs = r.get("data")
                        for rb in rbs:
                            try:
                                _b = Board.objects.get(
                                    LABPCOwner__id=b.LABPCOwner.id, boardLabID=rb["board_lab_id"])
                                if rb["power"] is not None:
                                    _b.statusPower = getStatusControl(
                                        rb["power"])
                                if rb["boot"] is not None:
                                    _b.statusBoot = getStatusControl(
                                        rb["boot"])
                                _b.save()
                            except Board.DoesNotExist:
                                print("Labpc[{0} ip={2}] not exist boardLabID[{1}]".format(
                                    b.LABPCOwner.id, rb["board_lab_id"], b.LABPCOwner.ipaddr))
                            except:
                                print("LAPBC Respose wrong format")
                bs = Board.objects.filter(
                    **sort_params,  isShareControl=True, isActivate=True)
            mydata = GetBoardsSerializer(bs, many=True)
            return Response(data=mydata.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"ok": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GetTokenAPI(APIView):
    """Get user token."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        print(request.user)
        token = Token.objects.get_or_create(user=request.user)
        print(token)
        return Response({"token": token[0].key}, status=status.HTTP_200_OK)


class SetControlBoardAPI(APIView):
    """Set control board by board ID."""
    authentication_classes = [SessionAuthentication]

    def get(self, request):
        print("request from " + str(request.user.username)
              if request.user.id else "request from anonymous")
        try:
            resp = {"ok": True, "message": "This is good"}
            sort_board_id = request.GET.get('board_id', None)
            sort_labpc_id = request.GET.get('labpc_id', None)
            sort_pcd_ip = request.GET.get('pcd_ip', None)
            sort_board_lab_id = request.GET.get('board_lab_id', None)
            sort_relay_id = request.GET.get('relay_id', None)
            using_by = request.GET.get('using_by', None)
            lock = request.GET.get('lock', False)
            control = request.GET.get("control", None)  # on or off

            if control is None or control.lower() not in ['off', 'on', 'boot', 'unboot']:
                raise ValueError("Need input control=on/off/boot/unboot")
            if None not in [sort_board_lab_id, sort_labpc_id, using_by] and all(ele == None for ele in [sort_relay_id, sort_board_id, sort_pcd_ip]):
                # lab and board id of lab
                try:
                    l = LABPC.objects.get(id=int(sort_labpc_id))
                    b = Board.objects.filter(
                        LABPCOwner=l, boardIdOnLab=sort_board_lab_id)
                except ObjectDoesNotExist:
                    raise ValueError("Labpc {0} is not exist or Board ID {1} in LABPC[{0}] not exist.".format(
                        sort_labpc_id, sort_board_lab_id))

                url = "http://%s:%d/api/control/boards/" % (
                    str(l.ipaddr), int(l.port))
                params = {}
                set_if_not_none(params, 'cmd', 'control')
                set_if_not_none(params, 'arg', control)
                set_if_not_none(params, 'board_lab_id', sort_board_lab_id)
                set_if_not_none(params, 'labpc_id', sort_labpc_id)
                try:
                    r = requests.get(url, params=params).json()
                    resp["data"] = r
                except:
                    raise ValueError("Failed request to %s" % url)
                print(json.dumps(resp, depth=4, sort_keys=True))
                return Response(resp, status=status.HTTP_200_OK)
            if None not in [sort_relay_id, sort_pcd_ip, sort_labpc_id, using_by] and sort_board_id is None:
                # lab id + pcd ip + relay id
                # send request to labpc ont care board type
                try:
                    l = LABPC.objects.get(id=int(sort_labpc_id))
                except ObjectDoesNotExist:
                    raise ValueError("Labpc %s is not exist" % (sort_labpc_id))

                # room = "labpc_" + str(sort_labpc_id) # get the room of the board
                # channel_layer = get_channel_layer()
                # async_to_sync(channel_layer.group_send)(
                # room,
                # {
                #     "type": "room_message",
                #     "from": sort_using_by,
                #     "to" : "labpc",
                #     "evt": "request",
                #     "message": {
                #         "cmd": "power",
                #         "arg": power,
                #         "pcd_ip": sort_pcd_ip,
                #         "labpc_id": sort_labpc_id,
                #         "relay_id" : sort_relay_id
                #     },
                # }
                # )
                url = "http://%s:%d/api/control/relay/" % (
                    str(l.ipaddr), int(l.port))
                params = {"cmd": "control", "arg": control, "pcd_ip": sort_pcd_ip,
                          "labpc_id": sort_labpc_id, "relay_id": sort_relay_id}
                try:
                    r = requests.get(url, params=params).json()
                except:
                    raise ValueError("Cannot connect to LABPC")
                print(json.dumps(r))
                resp["messase"] = r
                return Response(resp, status=status.HTTP_200_OK)

            if sort_board_id is None:
                raise ValueError("Need more input ex: board_id")
            try:
                b = Board.objects.get(id=int(sort_board_id))
            except Board.DoesNotExist:
                raise ValueError("Board is not exist")
            except:
                raise ValueError("Failed get board")
            if not b.isActivate:
                raise ValueError("Board is not activate")
            if b.usingBy == None and using_by is not None:
                b.lock = lock
            if b.lock and b.usingBy != using_by:
                raise ValueError(
                    "Board is using by %s. Unlock board firt." % (b.usingBy))
            if not b.isShareControl:
                raise ValueError("Board is not sharing")

            url = "http://%s:%d/api/control/boards/?" % (
                str(b.LABPCOwner.ipaddr), int(b.LABPCOwner.port))
            params = {"cmd": "control", "board_lab_id": b.boardLabID, "control": control, "pcd_ip": b.PCDOwner.id,
                      "labpc_id": b.LABPCOwner.id, "power_relay_id": b.powerSwitchRelayNumber, "boot_relay_id": b.accSwitchRelayNumber}
            try:
                r = requests.get(url, params=params).json()
            except:
                raise ValueError("Cannot connect to LABPC")

            room = "labpc_" + str(b.LABPCOwner.id) # get the room of the board
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                room,
                {
                    "type": "room_message",
                    "from": "Guest" if using_by == None else str(using_by),
                    "to" : "client",
                    "evt": "notify_control",
                    "message": {
                        "cmd": "control",
                        "arg": control,
                        "board_id": b.id
                    },
                }
            )

            return Response(r, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"ok": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        print(request.data)
        return Response('OK', status=status.HTTP_200_OK)


def index(request):
    """render for index page.

    Args:
        request: request message.

    """
    bs = Board.objects.filter(isShareControl=True, isActivate=True)
    ls = []
    data = {}
    data["error"] = []
    for b in bs:
        if b.LABPCOwner.id in ls:
            continue
        url = "http://%s:%d/api/status/boards/?" % (
            str(b.LABPCOwner.ipaddr), int(b.LABPCOwner.port))
        try:
            r = requests.get(url).json()
        except:
            r = {"ok": False, "error": "%s not respond" % (url)}
        if r.get("ok"):
            ls.append(b.LABPCOwner.id)
            rbs = r.get("data")
            for rb in rbs:
                try:
                    _b = Board.objects.get(LABPCOwner__id = b.LABPCOwner.id, boardLabID = rb["board_lab_id"])
                    if rb["power"] is not None:
                        _b.statusPower = getStatusControl(rb["power"])
                    if rb["boot"] is not None:
                        _b.statusBoot = getStatusControl(rb["boot"])
                    _b.save()
                except Board.DoesNotExist:
                    print("Labpc[{0} ip={2}] not exist boardLabID[{1}]".format(
                        b.LABPCOwner.id, rb["board_lab_id"], b.LABPCOwner.ipaddr))
                except:
                    print("LAPBC Response wrong format")
        else:
            data["error"].append("LAB_%s->" %
                                 (str(b.LABPCOwner.id)) + r.get("error"))
    bs = Board.objects.filter(isShareControl=True, isActivate=True)
    data["boards"] = bs
    return render(request, "myboard/index.html", data)


def room(request, room_name, board_id):
    """render for labPC room pages.

    Args:
        request: request message.
        room_name: generate from labPC ID.

    """
    try:
        l = LABPC.objects.get(id=room_name)
        b = Board.objects.get(id=board_id)
    except:
        return render(request, "myboard/page_not_found.html")

    if request.user.is_anonymous:
        try:
            guest = CustomUser.objects.get(username="guest")
            token = Token.objects.get(user=guest)
        except CustomUser.DoesNotExist:
            guest = CustomUser(username='guest', password=''.join(
                random.choice(string.ascii_lowercase) for i in range(10)))
            guest.save()
            token = Token.objects.get(user=guest)
            print(token.key)
    else:
        token = Token.objects.get(user=request.user)

    url = "http://%s:%d/api/status/boards/?" % (
        str(b.LABPCOwner.ipaddr), int(b.LABPCOwner.port))
    params = {"board_lab_id":b.boardLabID}
    try:
        r = requests.get(url,params=params).json()
    except:
        r = {"ok": False, "error": "%s not respond" % (url)}
    if r.get("ok"):
        try:
            data = r.get("data")
            if data["power"] is not None:
                b.statusPower = getStatusControl(data["power"])
            if data["boot"] is not None:
                b.statusBoot = getStatusControl(data["boot"])
            b.save()
            
        except Board.DoesNotExist:
            print("Labpc[{0} ip={2}] not exist boardLabID[{1}]".format(
                b.LABPCOwner.id, r["board_lab_id"], b.LABPCOwner.ipaddr))
        except:
            print("LAPBC Response wrong format")
    return render(
        request, "myboard/room.html", {
            "room_name": room_name,
            "my_token": token.key,
            "board": [b.id, b.statusPower, b.statusBoot],
        }
    )
