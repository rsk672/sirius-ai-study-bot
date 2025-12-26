MODEL = "intfloat/multilingual-e5-large"
DEVICE = "cpu"
EMBEDDING_API_URL = "http://localhost:7777/embeddings"
MODEL_DIMENSIONS = {
    "cointegrated/rubert-tiny2": 312,
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "intfloat/multilingual-e5-large": 1024,
    "Qwen/Qwen3-Embedding-0.6B": 1536,
}

# --- RAG / LLM (OpenRouter) ---
RAG_MODEL_NAME = "nex-agi/deepseek-v3.1-nex-n1:free"
RAG_BASE_URL = "https://openrouter.ai/api/v1"
RAG_TEMPERATURE = 0.3
RAG_MAX_TOKENS = 512
RAG_PROMPT_PATH = "rag/prompt.txt"

# HTTP settings
RAG_HTTP_TIMEOUT = 60.0

# Retrieval formatting
RAG_EMPTY_RETRIEVAL_TEXT = "NO_MATCHES"
RAG_DEFAULT_LABEL = "None"

# --- OCR (OpenRouter + Qwen-VL) ---
OCR_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OCR_VL_MODEL = "qwen/qwen3-vl-235b-a22b-instruct"

# Prompt
OCR_PROMPT_PATH = "ocr/ocr_prompt.txt"

# OCR request settings
OCR_LANGUAGE_HINT = "ru,en"
OCR_TIMEOUT = 120.0
OCR_MAX_TOKENS = 2000

# PDF processing defaults
OCR_PDF_DPI = 220
OCR_MIN_TEXT_CHARS_PER_PAGE = 80

# --- Database / Chroma ---
DB_DEBUG = False

SQL_DB_PATH = "sql.db"
CHROMA_COLLECTION_NAME = "inner_db"
DB_DEFAULT_LABEL = "None"

# используется только для генерации уникальных id чанков в chroma
DB_HASH_SALT = "iag!@#1239s0df0sde??|9kudfrlkhgovb040259jf@#!#!esksekies"
