"""
このファイルは、最初の画面読み込み時にのみ実行される初期化処理が記述されたファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import os
# Windows環境での文字エンコーディング問題を解決
os.environ['PYTHONIOENCODING'] = 'utf-8'
import logging
from logging.handlers import TimedRotatingFileHandler
from uuid import uuid4
import sys
import unicodedata
import shutil
from typing import Optional
from dotenv import load_dotenv
import streamlit as st
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
import utils
import constants as ct


############################################################
# 設定関連
############################################################
load_dotenv()


############################################################
# 関数定義
############################################################

def initialize() -> None:
    """
    画面読み込み時に実行する初期化処理
    """
    # 初期化データの用意
    initialize_session_state()
    # ログ出力用にセッションIDを生成
    initialize_session_id()
    # ログ出力の設定（セッションID生成後に実行）
    initialize_logger()
    # RAGのRetrieverを作成
    initialize_retriever()


def initialize_logger():
    """
    ログ出力の設定
    """
    os.makedirs(ct.LOG_DIR_PATH, exist_ok=True)
    
    logger = logging.getLogger(ct.LOGGER_NAME)

    if logger.hasHandlers():
        return

    # セッションIDが存在しない場合のデフォルト値を設定
    session_id = getattr(st.session_state, 'session_id', 'unknown')
    
    log_handler = TimedRotatingFileHandler(
        os.path.join(ct.LOG_DIR_PATH, ct.LOG_FILE),
        when="D",
        encoding="utf8"
    )
    formatter = logging.Formatter(
        f"[%(levelname)s] %(asctime)s line %(lineno)s, in %(funcName)s, session_id={session_id}: %(message)s"
    )
    log_handler.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(log_handler)


def initialize_session_id():
    """
    セッションIDの作成
    """
    if "session_id" not in st.session_state:
        st.session_state.session_id = uuid4().hex


def initialize_session_state():
    """
    初期化データの用意
    """
    if "messages" not in st.session_state:
        st.session_state.messages = []


def initialize_retriever():
    """
    Retrieverを作成
    """
    logger = logging.getLogger(ct.LOGGER_NAME)

    if "retriever" in st.session_state:
        return
    
    # ファイルパスの存在確認
    if not os.path.exists(ct.RAG_SOURCE_PATH):
        logger.error(f"データソースファイルが見つかりません: {ct.RAG_SOURCE_PATH}")
        raise FileNotFoundError(f"データソースファイルが見つかりません: {ct.RAG_SOURCE_PATH}")
    
    try:
        loader = CSVLoader(ct.RAG_SOURCE_PATH, encoding="utf-8-sig")
        docs = loader.load()
        
        if not docs:
            logger.warning("CSVファイルからドキュメントが読み込まれませんでした")
            raise ValueError("CSVファイルが空または無効です")
            
    except Exception as e:
        logger.error(f"CSVファイル読み込みエラー: {e}")
        raise

    # OSがWindowsの場合、Unicode正規化と、cp932（Windows用の文字コード）で表現できない文字を除去
    for doc in docs:
        doc.page_content = adjust_string(doc.page_content)
        for key in doc.metadata:
            doc.metadata[key] = adjust_string(doc.metadata[key])

    # OpenAI API キーの存在確認
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY環境変数が設定されていません")
        raise ValueError("OPENAI_API_KEY環境変数が設定されていません")
    
    embeddings = OpenAIEmbeddings()

    
    # データベースの状態を確認
    logger.info(f"processing db: {ct.DB_PATH}")
    db_exists = os.path.isdir(ct.DB_PATH)
    
    # すでに対象のデータベースが作成済みで、かつ作成から24時間以内の場合は読み込み、未作成またはデータベースが作成されてから24時間以上経った場合は新規作成する
    if db_exists:
        try:
            db_mtime = os.path.getmtime(ct.DB_PATH)
            threshold_time = utils.get_time(f"-{ct.DB_CACHE_DURATION_DAYS}d") # utils.pyに実装したget_time関数を使い、"now-24h"の時刻を取得
            if db_mtime > threshold_time:
                logger.info("データベースは既存のものを使用。")
                db = Chroma(persist_directory=ct.DB_PATH, embedding_function=embeddings)
            else:
                logger.info("データベースが古いため、新規作成する。")
                # 古いデータベースを削除してから新規作成
                shutil.rmtree(ct.DB_PATH)
                db = Chroma.from_documents(docs, embedding=embeddings, persist_directory=ct.DB_PATH)
        except OSError as e:
            logger.warning(f"データベースファイルアクセスエラー: {e}. 新規作成します。")
            db = Chroma.from_documents(docs, embedding=embeddings, persist_directory=ct.DB_PATH)
    else:
        logger.info("データベースが存在しないため、新規作成する。")
        db = Chroma.from_documents(docs, embedding=embeddings, persist_directory=ct.DB_PATH)
    
    retriever = db.as_retriever(search_kwargs={"k": ct.TOP_K})

    # BM25検索用のテキストデータ
    docs_text = []
    
    # ハイブリッド検索の整合性を保つため、データベースからテキストデータを取得
    logger.info("データベースからドキュメントを取得してBM25検索を構築")
    try:
        # データベース内の全ドキュメントを取得
        # Chromaのget()は{'documents': [doc1, doc2, ...], 'metadatas': [...], 'ids': [...]}の形式
        all_docs = db.get()
        docs_text = all_docs.get('documents', []) if all_docs else []
        
        if not docs_text:
            logger.error("データベースからドキュメントを取得できませんでした。ハイブリッド検索の整合性を保つため、処理を中断します。")
            raise ValueError("データベースからドキュメントを取得できませんでした")
        else:
            logger.info(f"データベースから{len(docs_text)}件のドキュメントを取得しました")
    except Exception as e:
        logger.error(f"データベースからのドキュメント取得に失敗: {e}. ハイブリッド検索の整合性を保つため、処理を中断します。")
        raise

    bm25_retriever = BM25Retriever.from_texts(
        docs_text,
        preprocess_func=utils.preprocess_func,
        k=ct.TOP_K
    )
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, retriever],
        weights=ct.RETRIEVER_WEIGHTS
    )

    st.session_state.retriever = ensemble_retriever


def adjust_string(s: str) -> str:
    """
    Windows環境でRAGが正常動作するよう調整
    
    Args:
        s: 調整を行う文字列
    
    Returns:
        調整を行った文字列
    """
    # 調整対象は文字列のみ
    if type(s) is not str:
        return s

    # OSがWindowsの場合、Unicode正規化と、cp932（Windows用の文字コード）で表現できない文字を除去
    if sys.platform.startswith("win"):
        s = unicodedata.normalize('NFC', s)
        s = s.encode("cp932", "ignore").decode("cp932")
        return s
    
    # OSがWindows以外の場合はそのまま返す
    return s