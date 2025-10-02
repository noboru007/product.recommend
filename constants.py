"""
このファイルは、固定の文字列や数値などのデータを変数として一括管理するファイルです。
"""
############################################################
# ライブラリの読み込み
############################################################
# import os
from pathlib import Path
# from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, TextLoader
from langchain_community.document_loaders.csv_loader import CSVLoader

############################################################
# 共通変数の定義
############################################################

# ベースディレクトリのパスを取得（このファイルが存在するディレクトリ）
BASE_DIR = Path(__file__).resolve().parent

# ==========================================
# 画面表示系
# ==========================================
APP_NAME = "対話型商品レコメンド生成AIアプリ"
USER_ICON_FILE_PATH = str(BASE_DIR / "images" / "user_icon.jpg")
AI_ICON_FILE_PATH = str(BASE_DIR / "images" / "ai_icon.jpg")
ERROR_ICON = ":material/error:"
CHAT_INPUT_HELPER_TEXT = "こちらからお探しの商品の特徴や名前を入力してください。"
SPINNER_TEXT = "レコメンドする商品の検討中..."


# ==========================================
# ログ出力系
# ==========================================
LOG_DIR_PATH = str(BASE_DIR / "logs")
LOGGER_NAME = "ApplicationLog"
LOG_FILE = "application.log"
APP_BOOT_MESSAGE = "アプリが起動されました。"

# ==========================================
# Retriever設定系
# ==========================================
TOP_K = 5
RETRIEVER_WEIGHTS = [0.5, 0.5] # BM25RetrieverとChromaの比重
DB_CACHE_DURATION_DAYS = 1  # データベースキャッシュの有効期間（日数）


# ==========================================
# RAG参照用のデータソース系
# ==========================================
RAG_SOURCE_PATH = str(BASE_DIR / "data" / "products.csv")
DB_PATH = str(BASE_DIR / "data" / ".db")

SUPPORTED_EXTENSIONS = {
    # ".pdf": PyMuPDFLoader,
    # ".docx": Docx2txtLoader,
    # ".txt": lambda path: TextLoader(path, encoding="utf-8"),
    ".csv": lambda path: CSVLoader(path, encoding="utf-8-sig") # 【問題1】CSVのFAQデータ読み込み用
}


# ==========================================
# 在庫管理系　【手順2】 在庫状況のメッセージ判定用
# ==========================================
STOCK_STATUS_FEW = "残りわずか"
STOCK_STATUS_NONE = "なし"


# ==========================================
# エラー・警告メッセージ
# ==========================================
COMMON_ERROR_MESSAGE = "このエラーが繰り返し発生する場合は、管理者にお問い合わせください。"
INITIALIZE_ERROR_MESSAGE = "初期化処理に失敗しました。"
CONVERSATION_LOG_ERROR_MESSAGE = "過去の会話履歴の表示に失敗しました。"
RECOMMEND_ERROR_MESSAGE = "商品レコメンドに失敗しました。"
LLM_RESPONSE_DISP_ERROR_MESSAGE = "商品情報の表示に失敗しました。"
REMAINING_STOCK_WARNING_MESSAGE = "ご好評につき、在庫数が残りわずかです。購入をご希望の場合、お早目のご注文をおすすめいたします。" # 【手順2】 在庫状況が「残りわずか」は黄色で警告を表示
SOLDOUT_ERROR_MESSAGE = "申し訳ございませんが、本商品は在庫切れとなっております。入荷までもうしばらくお待ちください。" # 【手順2】 在庫状況が「なし」は赤字でエラーを表示
