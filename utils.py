"""
このファイルは、画面表示以外の様々な関数定義のファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import logging
from typing import List
from sudachipy import tokenizer, dictionary
import constants as ct


############################################################
# 関数定義
############################################################

def build_error_message(message):
    """
    エラーメッセージと管理者問い合わせテンプレートの連結

    Args:
        message: 画面上に表示するエラーメッセージ

    Returns:
        エラーメッセージと管理者問い合わせテンプレートの連結テキスト
    """
    return "\n".join([message, ct.COMMON_ERROR_MESSAGE])


def preprocess_func(text: str) -> List[str]:
    """
    形態素解析による日本語の単語分割
    Args:
        text: 単語分割対象のテキスト
    
    Returns:
        単語分割を実施後のテキスト
    """
    logger = logging.getLogger(ct.LOGGER_NAME)

    try:
        tokenizer_obj = dictionary.Dictionary(dict="full").create()
        mode = tokenizer.Tokenizer.SplitMode.A
        tokens = tokenizer_obj.tokenize(text, mode)
        # セット変換でパフォーマンス向上
        words = list({token.surface() for token in tokens})
        return words
    except Exception as e:
        logger.warning(f"形態素解析エラー: {e}. 元のテキストを返します。")
        return [text]

def get_time(offset: str = None) -> float:
    """
    現在時刻または指定オフセット時刻のUNIXタイムスタンプ（float）を返す

    Args:
        offset (str, optional): "now", "0", "-3y4m5d6s", "+3y4m5d6s" などのオフセット指定。Noneの場合は現在時刻。

    Returns:
        float: UNIXタイムスタンプ（秒単位）

    Raises:
        Exception: パラメータが解読不能な場合
    """
    import time
    from datetime import datetime, timedelta

    now = time.time()

    # パラメータが未指定、"now"、"0"の場合は現在時刻
    if offset is None or str(offset).strip().lower() == "now" or str(offset).strip() == "0":
        return now

    offset_str = str(offset).strip()

    # プラス・マイナスの判定
    if offset_str[0] in "+-":
        sign = 1 if offset_str[0] == "+" else -1
        offset_body = offset_str[1:]
    else:
        # プラス・マイナスの指定が無い場合はデフォルトでプラス
        sign = 1
        offset_body = offset_str

    # 単位が一切無い場合（例: "3"や"-3"）はd（日）とみなす
    import re
    if re.fullmatch(r"\d+", offset_body):
        y, m, d, s = 0, 0, int(offset_body), 0
    else:
        # 正規表現で各単位を抽出
        pattern = r"(?:(\d+)y)?(?:(\d+)m)?(?:(\d+)d)?(?:(\d+)s)?"
        match = re.fullmatch(pattern, offset_body)
        if not match:
            raise Exception(f"get_time: 解読不能なパラメータ: {offset}")
        y = int(match.group(1)) if match.group(1) else 0
        m = int(match.group(2)) if match.group(2) else 0
        d = int(match.group(3)) if match.group(3) else 0
        s = int(match.group(4)) if match.group(4) else 0

        # すべて0の場合は例外
        if y == 0 and m == 0 and d == 0 and s == 0:
            raise Exception(f"get_time: 解読不能なパラメータ: {offset}")

    # 現在時刻をdatetimeに変換
    dt = datetime.fromtimestamp(now)

    # 年・月の加減算
    if y != 0 or m != 0:
        year = dt.year + sign * y
        month = dt.month + sign * m
        # 月が1～12の範囲になるよう調整
        while month > 12:
            year += 1
            month -= 12
        while month < 1:
            year -= 1
            month += 12
        # 日付が月末を超えないように調整
        day = min(dt.day, [31,
                           29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                           31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
        dt = dt.replace(year=year, month=month, day=day)

    # 日・秒の加減算
    dt = dt + timedelta(days=sign * d, seconds=sign * s)

    return dt.timestamp()