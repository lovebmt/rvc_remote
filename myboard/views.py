from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import GetBoardsSerializer
from .models import Board, LABPC , CustomUser
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import SessionAuthentication
from django.core.exceptions import ObjectDoesNotExist

import requests
import json

def gen_url(base,params):
    '''Gen url by merging parameters
        Parameter(s):
            params: The parametes using for generate url
        Return:
            ret: the url generated
    '''
    import urllib.parse
    ret = base + urllib.parse.urlencode(params)
    return ret
def set_if_not_none(mapping, key, value):
    if value is not None:
        mapping[key] = value
def get_user_by_request(request):
    """Get user by request"""

    try:
        lines = iter(request.META['HTTP_AUTHORIZATION'].split())
        for line in lines:
            if line == 'token':
                token_key = next(lines)
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return AnonymousUser()

class GetBoardsAPI(APIView):
    """Get list of user boards."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print(request.user)
        return Response(data = {"indev"},status=status.HTTP_200_OK)
def getPower(power):
    if power in [True, "ON", 'on']:
        return Board.StatusPower.POWER_ON
    else :
        return Board.StatusPower.POWER_OFF

class GetShareBoardsAPI(APIView):
    """Get list of shared boards."""

    def get(self, request):
        print("Get list share board by ",end="")
        print(request.user)
        try:
            
            sort_board_id = request.GET.get('board_id', None)
            sort_using_by = request.GET.get('using_by', None) 
            sort_labpc_id = request.GET.get('labpc_id', None) 
            sort_pcd_ip = request.GET.get('pcd_ip', None) 
            sort_board_type = request.GET.get('board_type', None)
            sort_board_lab_id = request.GET.get('board_lab_id', None)


            # The params tpsort by
            sort_params = {}
            set_if_not_none(sort_params, 'id', sort_board_id)
            set_if_not_none(sort_params, 'usingBy', sort_using_by)
            set_if_not_none(sort_params, 'LABPCOwner__id', sort_labpc_id)
            set_if_not_none(sort_params, 'PCDOwner__ipaddr', sort_pcd_ip)
            set_if_not_none(sort_params, 'boardType', sort_board_type)
            set_if_not_none(sort_params, 'boardLabID', sort_board_lab_id)
            
            # if None not in [sort_board_id]:
            #     b = Board.objects.get(id=sort_board_id,  isShareControl = True,isActivate =True)
            #     link = "http://" + str(b.LABPCOwner.ipaddr) + ":" + str(b.LABPCOwner.port) + "/api/status/boards/?"
            #     link = gen_url(link,{"board_lab_id":b.boardLabID})
            #     print(link)
            #     r = requests.get(link)
            #     print(r.text)
            #     #save DB
            # elif None not in [sort_labpc_id,sort_board_lab_id]:
            #     b = Board.objects.get(boardLabID=sort_board_lab_id, LABPCOwner__id = sort_labpc_id, isShareControl = True,isActivate =True)
            #     link = "http://" + str(b.LABPCOwner.ipaddr) + ":" + str(b.LABPCOwner.port) + "/api/status/boards/?"
            #     link = gen_url(link,{"board_lab_id":sort_board_lab_id})
            #     print(link)
            #     r = requests.get(link)
            #     print(r.text)
            #     #save DB
            # elif None not in [sort_labpc_id,sort_pcd_ip]:

            #     l = LABPC.objects.get(id=sort_labpc_id)
            #     link = "http://" + str(l.ipaddr) + ":" + str(l.port) + "/api/status/boards/?"
            #     link = gen_url(link,{"pcd_ip":sort_pcd_ip})
            #     print(link)
            #     r = requests.get(link)
            #     print(r.text)
            #     #save DB return share board
            #     #save
            #     bs = Board.objects.filter(LABPCOwner__id = sort_labpc_id, PCDOwner__ipaddr=sort_pcd_ip,  isShareControl = True,isActivate =True)
            # elif None not in [sort_labpc_id]:

            bs = Board.objects.filter(**sort_params,  isShareControl = True,isActivate =True)
            ls = []
            for b in bs:
                if b.LABPCOwner.id in ls:
                    continue
                link = "http://" + str(b.LABPCOwner.ipaddr) + ":" + str(b.LABPCOwner.port) + "/api/status/boards/?"
                link = gen_url(link,{})
                print(link)
                r = requests.get(link).json()
                if r.get("ok") :
                    ls.append(b.LABPCOwner.id)
                    rbs = r.get("data")
                    for rb in rbs:
                        print(rb)
                        try:
                            _b = Board.objects.get(LABPCOwner__id = b.LABPCOwner.id, boardLabID = rb["board_lab_id"])
                            _b.statusPower = getPower(rb["power"])
                            _b.save()
                        except Board.DoesNotExist:
                            print ("Labpc[{0} ip={2}] not exist boardLabID[{1}]".format(b.LABPCOwner.id,rb["board_lab_id"],b.LABPCOwner.ipaddr))
                #save
            bs = Board.objects.filter(**sort_params,  isShareControl = True,isActivate =True)
            mydata = GetBoardsSerializer(bs,many=True)
            return Response(data = mydata.data,status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e),status=status.HTTP_400_BAD_REQUEST)


class SetLockBoardAPI(APIView):
    """Set lock board"""

    authentication_classes = []

    def get(self, request):
        try:
            sort_board_id = request.GET.get('board_id', None)
            sort_using_by = request.GET.get('using_by', None)

            b = Board.objects.get(id=sort_board_id,isActivate =True)
            resp = {"ok": True,"stuff": "This is good"}
            if sort_using_by == None:
                resp = {"ok": True,"warning": "Should have input using_by"}
            if  not b.isShareControl:
                raise ValueError( {"ok": False,"error": "Board is not shared or used"})
            if b.usingBy is not None:
                raise ValueError( {"ok": False,"error": "Board is using by %s."%(b.usingBy)})
            b.usingBy =  sort_using_by
            b.isUsing = True
            b.save()
            return Response(resp,status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e),status=status.HTTP_200_OK)


class SetUnlockBoardAPI(APIView):
    """Set unlock board"""

    authentication_classes = []

    def get(self, request):
        try:
            sort_board_id = request.GET.get('board_id', None)
            sort_using_by = request.GET.get('using_by', None)
            b = Board.objects.get(id=sort_board_id,isActivate =True)
            resp = {"ok": True,"stuff": "This is good"}
            if b.usingBy!= sort_using_by:
                raise ValueError( {"ok": False,"error": "Board is using by %s."%(b.usingBy)})
            if b.isUsing is False:
                raise ValueError( {"ok": False,"error": "Board is not locking"})
            b.usingBy =  None
            b.isUsing = False
            b.save()
            return Response(resp,status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e),status=status.HTTP_200_OK)


class GetTokenAPI(APIView):
    """Get user token."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        print(request.user)
        token = Token.objects.get_or_create(user=request.user)
        print(token)
        return Response({"token": token[0].key}, status=status.HTTP_200_OK)

class SetControlBoardByBoardIDAPI(APIView):
    """Set control board by board ID."""
    authentication_classes = [SessionAuthentication]

    def get(self, request):
        print("request from " + str(request.user.username) if request.user.id else "request from anonymous")
        try:
            resp = {"ok": True,"stuff": "This is good"}
            sort_board_id = request.GET.get('board_id', None)
            sort_using_by = request.GET.get('using_by', None)
            sort_labpc_id = request.GET.get('labpc_id', None)
            sort_pcd_ip = request.GET.get('pcd_ip', None)
            sort_board_lab_id = request.GET.get('board_lab_id', None)
            sort_relay_id = request.GET.get('relay_id', None)
            power = request.GET.get("power", None)
            if power is None :
                raise ValueError({"ok": False,"error": "Need input power"})
            if None not in [sort_board_lab_id,sort_labpc_id] and all(ele == None for ele in [sort_relay_id,sort_board_id,sort_pcd_ip]):
                #lab and board id of lab
                try:
                    l = LABPC.objects.get(id=int(sort_labpc_id))
                    b = Board.objects.filter(LABPCOwner=l,boardIdOnLab=sort_board_lab_id)
                except ObjectDoesNotExist:
                    raise ValueError({"ok": False,"error": "Labpc {0} is not exist or Board ID {1} in LABPC[{0}] not exist.".format(sort_labpc_id,sort_board_id_in_lab)})
                
                link = "http://" + l.ipaddr + ":" + l.port + "/api/control/boards/"
                link = gen_url(link,{"cmd":"power","arg":power,"labpc_id":sort_labpc_id,"board_lab_id":sort_board_lab_id})
                r = requests.get(link).json()
                resp["stuff"] = r
                print(json.dumps(resp,depth=4, sort_keys=True))
                return Response(resp, status=status.HTTP_200_OK)

            if None not in [sort_relay_id,sort_pcd_ip,sort_labpc_id] and sort_board_id is None:
                #lab id + pcd ip + relay id
                # send request to labpc ont care board type
                try:
                    l = LABPC.objects.get(id=int(sort_labpc_id))
                except ObjectDoesNotExist:
                    raise ValueError({"ok": False,"error": "Labpc %s is not exist"%(sort_labpc_id)})
                
                
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
                link = "http://" + l.ipaddr + ":" + l.port + "/api/control/boards/"
                link = gen_url(link,{"cmd":"power","arg":power,"pcd_ip":sort_pcd_ip,"labpc_id":sort_labpc_id,"relay_id":sort_relay_id})
                print(link)
                r = requests.get(link).json()
                print(json.dumps(r))
                resp["messase"] = r
                return Response(resp, status=status.HTTP_200_OK)
            if sort_board_id is None :
                raise ValueError({"ok": False,"error": "Need more input ex: board_id"})
            b = Board.objects.get(id=int(sort_board_id))
            if not b.isActivate :
                raise ValueError({"ok": False,"error": "Board is not activate"})
            if b.usingBy!= sort_using_by:
                raise ValueError({"ok": False,"error": "Board is using by %s. Plz lock/unlock board to use."%(b.usingBy)})
            if not b.isShareControl:
                raise ValueError({"ok": False,"error": "Board is not sharing"})

            # room = "labpc_" + str(b.LABPCOwner.user.id) # get the room of the board
            # resp['mess']= "send to room %s"%(room)
            # channel_layer = get_channel_layer()
            # async_to_sync(channel_layer.group_send)(
            #     room,
            #     {
            #         "type": "room_message",
            #         "from": sort_using_by,
            #         "to" : "labpc",
            #         "evt": "request",
            #         "message": {
            #             "cmd": "power",
            #             "arg": power,
            #             "board_id": b.id,
            #             "pcd_id": b.PCDOwner.id,
            #             "relay_id" : b.powerSwitchRelayNumber
            #         },
            #     }
            # )
            link = "http://" + str(b.LABPCOwner.ipaddr) + ":" + str(b.LABPCOwner.port) + "/api/control/boards/?"
            link = gen_url(link,{"cmd":"power","board_lab_id":b.boardLabID,"arg":power,"pcd_ip":b.PCDOwner.id,"labpc_id":b.LABPCOwner.id,"relay_id":b.powerSwitchRelayNumber})
            print(link)
            r = requests.get(link).json()
            return Response(r, status=status.HTTP_200_OK)
        except Exception as e:
            return Response((e), status=status.HTTP_400_BAD_REQUEST)
    def post(self, request):
        print(request.data)
        return Response('OK', status=status.HTTP_200_OK)


def index(request):
    """render for index page.

    Args:
        request: request message.

    """
    bs = Board.objects.all()
    ls = []
    for b in bs:
        if b.LABPCOwner.id in ls:
            continue
        link = "http://" + str(b.LABPCOwner.ipaddr) + ":" + str(b.LABPCOwner.port) + "/api/status/boards/?"
        link = gen_url(link,{})
        print(link)
        r = requests.get(link).json()
        if r.get("ok") :
            ls.append(b.LABPCOwner.id)
            rbs = r.get("data")
            for rb in rbs:
                print(rb)
                try:
                    _b = Board.objects.get(LABPCOwner__id = b.LABPCOwner.id, boardLabID = rb["board_lab_id"])
                    _b.statusPower = getPower(rb["power"])
                    _b.save()
                except Board.DoesNotExist:
                    print ("Labpc[{0} ip={2}] not exist boardLabID[{1}]".format(b.LABPCOwner.id,rb["board_lab_id"],b.LABPCOwner.ipaddr))
    bs = Board.objects.all()                
    return render(request, "myboard/index.html",{"boards": bs})
def boards(request):
    return render(request, "myboard/boards.html")
import random
import string
def room(request, room_name,board_id):
    """render for labPC room pages.

    Args:
        request: request message.
        room_name: generate from labPC ID.

    """
    try:
        l = LABPC.objects.get(id=room_name)
        b = Board.objects.get(id=board_id)
    except :
        return render(request, "myboard/board_not_found.html")

    if request.user.is_anonymous:
        try:
            guest = CustomUser.objects.get(username="guest")
            token = Token.objects.get(user=guest)
        except CustomUser.DoesNotExist:
            guest = CustomUser(username='guest', password= ''.join(random.choice(string.ascii_lowercase) for i in range(10)))
            guest.save()
            token = Token.objects.get(user=guest)
            print(token.key)
    else:
        token = Token.objects.get(user=request.user)

    return render(
        request, "myboard/room.html", {
            "room_name": room_name,
            "my_token": token.key,
            "board_id":board_id,
        }
    )
