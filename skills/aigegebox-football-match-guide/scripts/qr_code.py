"""Dependency-free QR Code encoder for short UTF-8 URLs.

The poster renderer only needs byte-mode QR codes for a homepage or campaign
link. This module supports QR versions 1-6 with error correction level M.
"""

from __future__ import annotations

from typing import Iterable


# (number of blocks, total codewords per block, data codewords per block)
_M_BLOCKS = {
    1: ((1, 26, 16),),
    2: ((1, 44, 28),),
    3: ((1, 70, 44),),
    4: ((2, 50, 32),),
    5: ((2, 67, 43),),
    6: ((4, 43, 27),),
}

_ALIGNMENT = {
    1: (),
    2: (6, 18),
    3: (6, 22),
    4: (6, 26),
    5: (6, 30),
    6: (6, 34),
}


def _append_bits(bits: list[int], value: int, length: int) -> None:
    bits.extend((value >> index) & 1 for index in range(length - 1, -1, -1))


def _bits_to_int(bits: Iterable[int]) -> int:
    value = 0
    for bit in bits:
        value = (value << 1) | bit
    return value


def _bch_remainder(value: int, polynomial: int) -> int:
    value <<= polynomial.bit_length() - 1
    while value.bit_length() >= polynomial.bit_length():
        value ^= polynomial << (value.bit_length() - polynomial.bit_length())
    return value


def _format_bits(mask: int) -> int:
    # Error correction level M is binary 00 in QR format information.
    data = mask
    return ((data << 10) | _bch_remainder(data, 0x537)) ^ 0x5412


def _gf_mul(x: int, y: int) -> int:
    result = 0
    while y:
        if y & 1:
            result ^= x
        y >>= 1
        x <<= 1
        if x & 0x100:
            x ^= 0x11D
    return result


def _reed_solomon(data: list[int], degree: int) -> list[int]:
    generator = [1]
    root = 1
    for _ in range(degree):
        next_generator = [0] * (len(generator) + 1)
        for index, coefficient in enumerate(generator):
            next_generator[index] ^= coefficient
            next_generator[index + 1] ^= _gf_mul(coefficient, root)
        generator = next_generator
        root = _gf_mul(root, 2)
    remainder = [0] * degree
    for value in data:
        factor = value ^ remainder[0]
        remainder = remainder[1:] + [0]
        for index, coefficient in enumerate(generator[1:]):
            remainder[index] ^= _gf_mul(coefficient, factor)
    return remainder


def _make_codewords(payload: str, version: int) -> list[int]:
    blocks = _M_BLOCKS[version]
    data_capacity = sum(count * data_words for count, _, data_words in blocks)
    raw = payload.encode("utf-8")
    bits: list[int] = []
    _append_bits(bits, 0b0100, 4)  # byte mode
    if len(raw) >= 256:
        raise ValueError("二维码链接过长，请使用更短的链接")
    _append_bits(bits, len(raw), 8)
    for value in raw:
        _append_bits(bits, value, 8)
    capacity_bits = data_capacity * 8
    if len(bits) > capacity_bits:
        raise ValueError("二维码链接过长，请使用更短的链接")
    bits.extend([0] * min(4, capacity_bits - len(bits)))
    bits.extend([0] * ((8 - len(bits) % 8) % 8))
    codewords = [_bits_to_int(bits[index:index + 8]) for index in range(0, len(bits), 8)]
    pad = (0xEC, 0x11)
    pad_index = 0
    while len(codewords) < data_capacity:
        codewords.append(pad[pad_index % 2])
        pad_index += 1

    data_blocks: list[list[int]] = []
    ecc_blocks: list[list[int]] = []
    offset = 0
    for count, total_words, data_words in blocks:
        for _ in range(count):
            block = codewords[offset:offset + data_words]
            offset += data_words
            data_blocks.append(block)
            ecc_blocks.append(_reed_solomon(block, total_words - data_words))
    result: list[int] = []
    for index in range(max(map(len, data_blocks))):
        result.extend(block[index] for block in data_blocks if index < len(block))
    for index in range(max(map(len, ecc_blocks))):
        result.extend(block[index] for block in ecc_blocks if index < len(block))
    return result


def _blank_matrix(version: int) -> tuple[list[list[bool | None]], list[list[bool]]]:
    size = version * 4 + 17
    matrix: list[list[bool | None]] = [[None] * size for _ in range(size)]
    reserved = [[False] * size for _ in range(size)]

    def set_module(row: int, col: int, value: bool) -> None:
        if 0 <= row < size and 0 <= col < size:
            matrix[row][col] = value
            reserved[row][col] = True

    def finder(row: int, col: int) -> None:
        for r in range(-1, 8):
            for c in range(-1, 8):
                if 0 <= row + r < size and 0 <= col + c < size:
                    dark = 0 <= r <= 6 and 0 <= c <= 6 and (r in {0, 6} or c in {0, 6} or (2 <= r <= 4 and 2 <= c <= 4))
                    set_module(row + r, col + c, dark)

    finder(0, 0)
    finder(size - 7, 0)
    finder(0, size - 7)

    for index in range(8, size - 8):
        if matrix[6][index] is None:
            set_module(6, index, index % 2 == 0)
        if matrix[index][6] is None:
            set_module(index, 6, index % 2 == 0)

    for row in _ALIGNMENT[version]:
        for col in _ALIGNMENT[version]:
            if matrix[row][col] is not None:
                continue
            for r in range(-2, 3):
                for c in range(-2, 3):
                    set_module(row + r, col + c, max(abs(r), abs(c)) != 1)

    # Reserve format information areas and the fixed dark module.
    for index in range(9):
        if matrix[index][8] is None:
            reserved[index][8] = True
        if matrix[8][index] is None:
            reserved[8][index] = True
    for index in range(8):
        reserved[8][size - 1 - index] = True
        reserved[size - 1 - index][8] = True
    set_module(size - 8, 8, True)
    return matrix, reserved


def _mask(mask: int, row: int, col: int) -> bool:
    if mask == 0:
        return (row + col) % 2 == 0
    if mask == 1:
        return row % 2 == 0
    if mask == 2:
        return col % 3 == 0
    if mask == 3:
        return (row + col) % 3 == 0
    if mask == 4:
        return (row // 2 + col // 3) % 2 == 0
    if mask == 5:
        return (row * col) % 2 + (row * col) % 3 == 0
    if mask == 6:
        return ((row * col) % 2 + (row * col) % 3) % 2 == 0
    return ((row * col) % 3 + (row + col) % 2) % 2 == 0


def _add_data(matrix: list[list[bool | None]], reserved: list[list[bool]], codewords: list[int], mask: int) -> None:
    bits: list[int] = []
    for value in codewords:
        _append_bits(bits, value, 8)
    size = len(matrix)
    bit_index = 0
    col = size - 1
    upward = True
    while col > 0:
        if col == 6:
            col -= 1
        rows = range(size - 1, -1, -1) if upward else range(size)
        for row in rows:
            for current_col in (col, col - 1):
                if reserved[row][current_col]:
                    continue
                value = bits[bit_index] if bit_index < len(bits) else 0
                bit_index += 1
                matrix[row][current_col] = bool(value ^ _mask(mask, row, current_col))
        upward = not upward
        col -= 2


def _penalty(matrix: list[list[bool | None]]) -> int:
    size = len(matrix)
    score = 0
    for row in matrix:
        run_color, run_length = row[0], 1
        for value in row[1:]:
            if value == run_color:
                run_length += 1
            else:
                if run_length >= 5:
                    score += 3 + run_length - 5
                run_color, run_length = value, 1
        if run_length >= 5:
            score += 3 + run_length - 5
    for col in range(size):
        run_color, run_length = matrix[0][col], 1
        for row in range(1, size):
            value = matrix[row][col]
            if value == run_color:
                run_length += 1
            else:
                if run_length >= 5:
                    score += 3 + run_length - 5
                run_color, run_length = value, 1
        if run_length >= 5:
            score += 3 + run_length - 5
    for row in range(size - 1):
        for col in range(size - 1):
            value = matrix[row][col]
            if matrix[row + 1][col] == value and matrix[row][col + 1] == value and matrix[row + 1][col + 1] == value:
                score += 3
    dark = sum(1 for row in matrix for value in row if value)
    score += int(abs(100 * dark / (size * size) - 50) // 5 * 10)
    return score


def _write_format(matrix: list[list[bool | None]], mask: int) -> None:
    size = len(matrix)
    bits = _format_bits(mask)
    for index in range(15):
        bit = bool((bits >> index) & 1)
        if index < 6:
            matrix[index][8] = bit
        elif index < 8:
            matrix[index + 1][8] = bit
        else:
            matrix[size - 15 + index][8] = bit
        if index < 8:
            matrix[8][size - index - 1] = bit
        elif index < 9:
            matrix[8][15 - index] = bit
        else:
            matrix[8][15 - index - 1] = bit
    matrix[size - 8][8] = True


def qr_matrix(payload: str) -> list[list[bool]]:
    """Return a QR matrix without the quiet zone, using ECC level M."""
    raw_length = len(payload.encode("utf-8"))
    version = next((version for version in _M_BLOCKS if 2 + raw_length <= sum(count * data_words for count, _, data_words in _M_BLOCKS[version])), None)
    if version is None:
        raise ValueError("二维码链接过长，请使用更短的链接")
    codewords = _make_codewords(payload, version)
    candidates: list[tuple[int, list[list[bool | None]]]] = []
    for mask in range(8):
        matrix, reserved = _blank_matrix(version)
        _add_data(matrix, reserved, codewords, mask)
        _write_format(matrix, mask)
        candidates.append((_penalty(matrix), matrix))
    matrix = min(candidates, key=lambda item: item[0])[1]
    return [[bool(value) for value in row] for row in matrix]
