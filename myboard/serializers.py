from rest_framework import serializers
from .models import Board

class GetAllBoardsOfByHolderSerializer(serializers.ModelSerializer):
    """Get all boards of by Holder and generate json format."""

    def to_representation(self, instance):
        return {
            "user_id": instance.id,
            "holder": "anonymous" if instance.holder == None else instance.user.username,
            "boards": [
                {
                    "id": board.id,
                    "name": str(board.displayName),
                    "stt": str("ON" if board.statusPower == Board.StatusPower.POWER_ON else "OFF"),
                }
                for board in instance.board_set.all()
            ],
        }


class GetBoardsSerializer(serializers.ModelSerializer):
    """Get all board status by board ID and generate json format."""

    def to_representation(self, board):
        print("Serializing board:",end="")
        print(board)
        return {
            'board_id': board.id,
            'board_lab_id' : board.boardLabID,
            'name': board.displayName,
            'type': board.boardType,
            'status_power': "ON" if board.statusPower == Board.StatusPower.POWER_ON else "OFF",
            'status_boot': "BOOT" if board.statusBoot == Board.StatusBoot.BOOT else "UNBOOT",
            'LABC_owner' : board.LABPCOwner.username,
            'PCD_address' : board.PCDOwner.ipaddr,
            'power_relay_number' : board.powerSwitchRelayNumber,
            'acc_relay_number': board.accSwitchRelayNumber,
            'holder': "anonymous" if board.holder is None else board.holder.username,
            'using': board.isUsing,
            'using_by' : board.usingBy if board.usingBy else "Unknow",
            'sharing': board.isShareControl,
        }
