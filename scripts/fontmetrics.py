"""Character widths (measured in Inter on the frontend's canvas).

Used for a node's initial size and for the width at which a whole title is visible.
Characters missing from the tables (CJK, etc.) are estimated the way the frontend falls back:
character count x font size x 0.6.

MarkdownNote body widths (md_char_w): the body is 10px Inter. Per-character widths were measured in the
frontend's DOM (Chrome on Linux rounds each character to an integer, which is wider than scaling the 1 em
ratio; the wider value is used). Bold heading widths are measured at 100px and rounded up for the size.
CJK and full-width characters are 1 em, emoji 1.37 em (Windows' Meiryo and Segoe UI Emoji; wider than Yu Gothic UI).
"""

import math

TITLE_14 = {"0": 9, "1": 6, "2": 9, "3": 9, "4": 9, "5": 8, "6": 9, "7": 8, "8": 9, "9": 9, " ": 4, "!": 4, "\"": 7, "#": 9, "$": 9, "%": 14, "&": 9, "'": 4, "(": 5, ")": 5, "*": 7, "+": 9, ",": 4, "-": 6, ".": 4, "/": 5, ":": 4, ";": 4, "<": 9, "=": 9, ">": 9, "?": 7, "@": 14, "A": 10, "B": 9, "C": 10, "D": 10, "E": 8, "F": 8, "G": 10, "H": 10, "I": 4, "J": 8, "K": 9, "L": 8, "M": 13, "N": 11, "O": 11, "P": 9, "Q": 11, "R": 9, "S": 9, "T": 9, "U": 10, "V": 10, "W": 14, "X": 10, "Y": 10, "Z": 9, "[": 5, "\\": 5, "]": 5, "^": 7, "_": 6, "`": 5, "a": 8, "b": 9, "c": 8, "d": 9, "e": 8, "f": 5, "g": 9, "h": 8, "i": 3, "j": 3, "k": 8, "l": 3, "m": 12, "n": 8, "o": 8, "p": 9, "q": 9, "r": 5, "s": 7, "t": 5, "u": 8, "v": 8, "w": 11, "x": 8, "y": 8, "z": 8, "{": 6, "|": 5, "}": 6, "~": 9}
LABEL_12 = {"0": 8, "1": 5, "2": 7, "3": 7, "4": 8, "5": 7, "6": 7, "7": 7, "8": 7, "9": 7, " ": 3, "!": 3, "\"": 6, "#": 8, "$": 8, "%": 12, "&": 8, "'": 4, "(": 4, ")": 4, "*": 6, "+": 8, ",": 3, "-": 6, ".": 3, "/": 4, ":": 3, ";": 4, "<": 8, "=": 8, ">": 8, "?": 6, "@": 12, "A": 8, "B": 8, "C": 9, "D": 9, "E": 7, "F": 7, "G": 9, "H": 9, "I": 3, "J": 7, "K": 8, "L": 7, "M": 11, "N": 9, "O": 9, "P": 8, "Q": 9, "R": 8, "S": 8, "T": 8, "U": 9, "V": 8, "W": 12, "X": 8, "Y": 8, "Z": 8, "[": 4, "\\": 4, "]": 4, "^": 6, "_": 5, "`": 4, "a": 7, "b": 7, "c": 7, "d": 7, "e": 7, "f": 4, "g": 7, "h": 7, "i": 3, "j": 3, "k": 7, "l": 3, "m": 11, "n": 7, "o": 7, "p": 7, "q": 7, "r": 5, "s": 6, "t": 4, "u": 7, "v": 7, "w": 10, "x": 7, "y": 7, "z": 7, "{": 5, "|": 4, "}": 5, "~": 8}


def width(s, table, px):
    return sum(table.get(ch, px * 0.6) for ch in s or "")


def title_width(s):
    return width(s, TITLE_14, 14)


def label_width(s):
    return width(s, LABEL_12, 12)


MD_10 = {" ": 3, "!": 3, "\"": 5, "#": 6, "$": 6, "%": 10, "&": 6, "'": 3, "(": 4, ")": 4, "*": 5, "+": 7, ",": 3, "-": 5, ".": 3, "/": 4, "0": 6, "1": 4, "2": 6, "3": 6, "4": 6, "5": 6, "6": 6, "7": 6, "8": 6, "9": 6, ":": 3, ";": 3, "<": 7, "=": 7, ">": 7, "?": 5, "@": 10, "A": 7, "B": 7, "C": 7, "D": 7, "E": 6, "F": 6, "G": 7, "H": 7, "I": 3, "J": 6, "K": 7, "L": 6, "M": 9, "N": 8, "O": 8, "P": 6, "Q": 8, "R": 6, "S": 6, "T": 6, "U": 7, "V": 7, "W": 10, "X": 7, "Y": 7, "Z": 6, "[": 4, "\\": 4, "]": 4, "^": 5, "_": 5, "`": 3, "a": 6, "b": 6, "c": 6, "d": 6, "e": 6, "f": 4, "g": 6, "h": 6, "i": 2, "j": 2, "k": 5, "l": 2, "m": 9, "n": 6, "o": 6, "p": 6, "q": 6, "r": 4, "s": 5, "t": 3, "u": 6, "v": 6, "w": 8, "x": 5, "y": 6, "z": 6, "{": 4, "|": 3, "}": 4, "~": 7}
MD_BOLD_10 = {" ": 2, "!": 3, "\"": 6, "#": 6, "$": 7, "%": 10, "&": 7, "'": 3, "(": 4, ")": 4, "*": 6, "+": 7, ",": 3, "-": 5, ".": 3, "/": 4, "0": 7, "1": 4, "2": 6, "3": 6, "4": 7, "5": 6, "6": 7, "7": 6, "8": 7, "9": 7, ":": 3, ";": 3, "<": 7, "=": 7, ">": 7, "?": 6, "@": 10, "A": 7, "B": 7, "C": 7, "D": 7, "E": 6, "F": 6, "G": 8, "H": 7, "I": 3, "J": 6, "K": 7, "L": 6, "M": 9, "N": 8, "O": 8, "P": 6, "Q": 8, "R": 7, "S": 7, "T": 7, "U": 7, "V": 7, "W": 10, "X": 7, "Y": 7, "Z": 7, "[": 4, "\\": 4, "]": 4, "^": 5, "_": 5, "`": 4, "a": 6, "b": 6, "c": 6, "d": 6, "e": 6, "f": 4, "g": 6, "h": 6, "i": 3, "j": 3, "k": 6, "l": 3, "m": 9, "n": 6, "o": 6, "p": 6, "q": 6, "r": 4, "s": 6, "t": 4, "u": 6, "v": 6, "w": 9, "x": 6, "y": 6, "z": 6, "{": 5, "|": 4, "}": 5, "~": 7}
MD_BOLD_EM = {" ": 21, "!": 25, "\"": 47, "#": 63, "$": 65, "%": 94, "&": 65, "'": 27, "(": 33, ")": 33, "*": 54, "+": 65, ",": 24, "-": 44, ".": 24, "/": 36, "0": 65, "1": 39, "2": 60, "3": 62, "4": 66, "5": 60, "6": 62, "7": 55, "8": 61, "9": 62, ":": 24, ";": 25, "<": 65, "=": 65, ">": 65, "?": 57, "@": 101, "A": 71, "B": 64, "C": 73, "D": 70, "E": 61, "F": 58, "G": 74, "H": 72, "I": 26, "J": 56, "K": 69, "L": 56, "M": 89, "N": 73, "O": 75, "P": 63, "Q": 75, "R": 65, "S": 65, "T": 64, "U": 70, "V": 71, "W": 100, "X": 70, "Y": 69, "Z": 63, "[": 33, "\\": 36, "]": 33, "^": 46, "_": 48, "`": 30, "a": 55, "b": 60, "c": 56, "d": 60, "e": 56, "f": 37, "g": 60, "h": 59, "i": 25, "j": 25, "k": 55, "l": 25, "m": 88, "n": 59, "o": 58, "p": 60, "q": 60, "r": 37, "s": 52, "t": 37, "u": 59, "v": 55, "w": 82, "x": 54, "y": 55, "z": 52, "{": 44, "|": 35, "}": 44, "~": 65}   # 1 em = 100
MD_MONO_EM = 55   # monospace (Windows' Consolas); rounds to 6 at 10px


def is_wide(ch):
    """Japanese, Chinese, Korean and full-width characters."""
    c = ord(ch)
    return (0x1100 <= c <= 0x115F or 0x2E80 <= c <= 0xA4CF or 0xAC00 <= c <= 0xD7A3
            or 0xF900 <= c <= 0xFAFF or 0xFE30 <= c <= 0xFE4F or 0xFF00 <= c <= 0xFF60
            or 0xFFE0 <= c <= 0xFFE6)


def is_emoji(ch):
    c = ord(ch)
    return c >= 0x1F000 or 0x2600 <= c <= 0x27BF


def md_char_w(ch, size=10, bold=False, mono=False):
    """Width in px of one character in a MarkdownNote body."""
    if ch in "\ufe0f\u200d":
        return 0
    if is_wide(ch):
        em = 100
    elif is_emoji(ch):
        em = 137
    elif mono:
        em = MD_MONO_EM
    elif size == 10 and ch in MD_10:
        return (MD_BOLD_10 if bold else MD_10)[ch]
    elif bold:
        em = MD_BOLD_EM.get(ch, 100)
    else:
        em = 100   # characters missing from the table (é, —, →, etc.)
    return math.ceil(em * size / 100 - 1e-9)
