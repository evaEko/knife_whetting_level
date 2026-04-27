import ctx
from states.level import get_board_level


def set_board_level():
    ctx.board_offset = get_board_level()
    print(f"ctx.board_offset set to: {ctx.board_offset}")
