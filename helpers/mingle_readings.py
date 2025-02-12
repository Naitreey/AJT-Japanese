# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import io
import re
from collections.abc import Iterable
from typing import NamedTuple, Final, Union

MULTIPLE_READING_SEP: Final[str] = "・"


class SplitFurigana(NamedTuple):
    head: str
    reading: str
    suffix: str


class NoFurigana(str):

    @property
    def head(self):
        return self

    reading = head


class WordReading(NamedTuple):
    word: str
    reading: str


def strip_non_jp_furigana(expr: str) -> str:
    """Non-japanese furigana is not real furigana. Strip it."""
    return re.sub(r"\[[^ぁ-ゖァ-ヺｧ-ﾝ]+]", "", expr)


def find_head_reading_suffix(text: str) -> Union[SplitFurigana, NoFurigana]:
    """
    Locate where furigana starts and ends, return the three parts.
    Return text back if it doesn't contain furigana.
    """
    furigana_start, furigana_end = -1, -1
    for i, c in enumerate(text):
        if c == "[":
            furigana_start = i
        if c == "]":
            furigana_end = i
            break
    if 0 < furigana_start < furigana_end:
        return SplitFurigana(text[:furigana_start], text[furigana_start + 1 : furigana_end], text[furigana_end + 1 :])
    else:
        return NoFurigana(text)


def iter_split_parts(text: str) -> Iterable[Union[SplitFurigana, NoFurigana]]:
    while text and (part := find_head_reading_suffix(text)):
        yield part
        if isinstance(part, NoFurigana):
            break
        text = part.suffix


def decompose_word(text: str) -> SplitFurigana:
    """
    Takes furigana notation, splits it into (head, reading, suffix).
    "辛[から]い" == (head='辛', reading='から', suffix='い')
    "南[みなみ]千[ち]秋[あき]" == (head='南千秋', reading='みなみちあき', suffix='')
    """
    head, reading, suffix = io.StringIO(), io.StringIO(), io.StringIO()
    for num, part in enumerate(iter_split_parts(text)):
        if isinstance(part, NoFurigana) and num > 0:
            suffix.write(part)
        else:
            head.write(part.head)
            reading.write(part.reading)
    return SplitFurigana(head.getvalue(), reading.getvalue(), suffix.getvalue())


def tie_inside_furigana(s: str) -> str:
    def fixup(m: re.Match):
        return m.group().replace(" ", MULTIPLE_READING_SEP)

    return re.sub(r"\[[^\[\]]+?]", fixup, s)


def whitespace_split(furigana_notation: str) -> list[str]:
    """
    Splits text by whitespace, except whitespace inside furigana.
    """
    return tie_inside_furigana(furigana_notation).split()


def word_reading(text: str) -> WordReading:
    """
    Takes furigana notation, splits it into (word, reading).
    """
    word, reading = [], []
    for split in map(decompose_word, whitespace_split(text)):
        word.append(split.head + split.suffix)
        reading.append(split.reading + split.suffix)
    word, reading = "".join(word), "".join(reading)
    return WordReading(word, reading) if (reading and word != reading) else WordReading(text, "")


def pairs(seq: list):
    yield from zip(seq, seq[1:])


def mingle_readings(words_furigana: list[str], *, sep: str = ", ") -> str:
    """
    Takes several furigana notations, packs them into one, with readings separated by sep.

    readings = ["辛[から]い", "辛[つら]い",]
    output = " 辛[から, つら]い"
    """

    assert len(words_furigana) > 1

    packs = []
    split = list(map(whitespace_split, words_furigana))

    if any(len(x) != len(y) for x, y in pairs(split)):
        # When notations are inconsistent, don't attempt further parsing.
        return words_furigana[0]

    for first, *rest in zip(*split):
        first = decompose_word(first)
        words_furigana = sep.join(dict.fromkeys(word.reading for word in (first, *map(decompose_word, rest))))
        packs.append(f" {first.head}[{words_furigana}]{first.suffix}" if words_furigana != first.head else first.head)
    return "".join(packs)


# Debug
##########################################################################


def main():
    assert whitespace_split(" 有[あ]り 得[う]る") == ["有[あ]り", "得[う]る"]

    assert strip_non_jp_furigana("悪[わる][1223]い[2]") == "悪[わる]い"

    assert decompose_word("故郷[こきょう]") == SplitFurigana(head="故郷", reading="こきょう", suffix="")
    assert decompose_word("有[あ]り") == SplitFurigana(head="有", reading="あ", suffix="り")
    assert decompose_word("ひらがな") == SplitFurigana(head="ひらがな", reading="ひらがな", suffix="")
    assert decompose_word("南[みなみ]千[ち]秋[あき]") == SplitFurigana(head="南千秋", reading="みなみちあき", suffix="")

    assert word_reading("有[あ]り 得[う]る") == WordReading(word="有り得る", reading="ありうる")
    assert word_reading("有る") == WordReading(word="有る", reading="")
    assert word_reading("お 前[まい<br>まえ<br>めえ]") == WordReading(word="お前", reading="おまい<br>まえ<br>めえ")
    assert word_reading("もうお 金[かね]が 無[な]くなりました。") == WordReading(
        word="もうお金が無くなりました。", reading="もうおかねがなくなりました。"
    )
    assert word_reading(
        "妹[いもうと]は 自分[じぶん]の 我[わ]が 儘[まま]が 通[とお]らないと、すぐ 拗[す]ねる。"
    ) == WordReading("妹は自分の我が儘が通らないと、すぐ拗ねる。", "いもうとはじぶんのわがままがとおらないと、すぐすねる。")

    assert (
        mingle_readings([" 有[あ]り 得[う]る", " 有[あ]り 得[え]る", " 有[あ]り 得[え]る"]) == " 有[あ]り 得[う, え]る"
    )
    assert mingle_readings([" 故郷[こきょう]", " 故郷[ふるさと]"]) == " 故郷[こきょう, ふるさと]"
    assert mingle_readings(["お 前[まえ]", "お 前[めえ]"]) == "お 前[まえ, めえ]"
    assert mingle_readings([" 言[い]い 分[ぶん]", " 言い分[いーぶん]"]) == " 言[い]い 分[ぶん]"
    print("Passed.")


if __name__ == "__main__":
    main()
