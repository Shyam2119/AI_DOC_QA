import os
import re
import logging
from typing import List, Tuple, Optional
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _clean_filename(raw: str) -> str:
    """Strip session UUID prefix (36 chars + underscore) from stored filename."""
    if len(raw) > 37 and raw[36] == '_':
        return raw[37:]
    return raw


def _sentences(text: str) -> List[str]:
    """Split text into clean sentences of at least 15 chars."""
    parts = re.split(r'(?<=[.!?])\s+', text.replace('\n', ' '))
    return [s.strip() for s in parts if len(s.strip()) >= 15]


def _bullet_format(items: List[str], max_items: int = 8) -> str:
    seen, result = set(), []
    for item in items:
        norm = item.lower().strip()
        if norm not in seen and len(item) > 10:
            seen.add(norm)
            result.append(f"• {item.rstrip('.')}.")
        if len(result) >= max_items:
            break
    return '\n'.join(result)


# ─── Query type detection ───────────────────────────────────────────────────────

SUMMARY_KW   = {"summarize", "summary", "summarise", "overview", "main points",
                "key points", "highlights", "brief", "outline", "what is this about",
                "what does this document", "describe the document", "tldr", "tl;dr"}
LIST_KW      = {"list", "what are all", "enumerate", "give me all", "show all",
                "what skills", "what technologies", "what tools", "what languages",
                "all the"}
COMPARE_KW   = {"compare", "difference", "vs", "versus", "contrast", "similar"}
DEFINE_KW    = {"define", "what is", "what does", "meaning of", "explain what"}
HOWMANY_KW   = {"how many", "count of", "number of", "total"}
CONTACT_KW   = {"email", "phone", "contact", "address", "linkedin", "github",
                "website", "url", "mobile", "number"}


def _detect_query_type(q: str) -> str:
    ql = q.lower()
    if any(k in ql for k in SUMMARY_KW):   return "summary"
    if any(k in ql for k in LIST_KW):      return "list"
    if any(k in ql for k in COMPARE_KW):   return "compare"
    if any(k in ql for k in DEFINE_KW):    return "define"
    if any(k in ql for k in HOWMANY_KW):   return "count"
    if any(k in ql for k in CONTACT_KW):   return "contact"
    return "factual"


# ─── RAGService ────────────────────────────────────────────────────────────────

class RAGService:
    def __init__(self):
        print("[RAG] Loading embedding model (all-MiniLM-L6-v2)...", flush=True)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        print("[RAG] ✅ Embeddings ready.", flush=True)
        self._qa_pipeline = None   # lazy — loads on first factual question

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=80,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    # ── QA pipeline (extractive) ──────────────────────────────────────────────
    def _get_qa(self):
        if self._qa_pipeline is None:
            print("[RAG] Loading QA model (tinyroberta-squad2)...", flush=True)
            from transformers import pipeline as hf_pipeline
            self._qa_pipeline = hf_pipeline(
                "question-answering",
                model="deepset/tinyroberta-squad2",
                device=-1,
            )
            print("[RAG] ✅ QA model ready.", flush=True)
        return self._qa_pipeline

    # ── PDF processing ────────────────────────────────────────────────────────
    def process_pdf(self, file_path: str, vector_store_path: str) -> Tuple[int, int]:
        print(f"[RAG] Loading PDF: {file_path}", flush=True)
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        page_count = len(pages)
        for i, page in enumerate(pages):
            page.metadata["page_number"] = i + 1
            page.metadata["source_file"] = Path(file_path).name
        chunks = self.text_splitter.split_documents(pages)
        chunk_count = len(chunks)
        print(f"[RAG] {page_count} pages → {chunk_count} chunks", flush=True)
        vs = FAISS.from_documents(chunks, self.embeddings)
        vs.save_local(vector_store_path)
        print(f"[RAG] ✅ Saved → {vector_store_path}", flush=True)
        return page_count, chunk_count

    # ── Vector store helpers ──────────────────────────────────────────────────
    def load_vector_store(self, path: str) -> FAISS:
        return FAISS.load_local(path, self.embeddings, allow_dangerous_deserialization=True)

    def merge_vector_stores(self, paths: List[str]) -> FAISS:
        if not paths:
            raise ValueError("No vector store paths provided")
        base = self.load_vector_store(paths[0])
        for p in paths[1:]:
            base.merge_from(self.load_vector_store(p))
        return base

    # ── Answer builders by type ───────────────────────────────────────────────
    def _answer_summary(self, docs) -> str:
        lines = []
        for doc in docs[:4]:
            lines.extend(_sentences(doc.page_content)[:2])
        bullets = _bullet_format(lines, max_items=7)
        return f"**Key points from the document:**\n\n{bullets}"

    def _answer_list(self, question: str, docs) -> str:
        context = " ".join(d.page_content for d in docs)[:3000]
        # Try extractive QA first; if confidence low, return raw lines
        try:
            result = self._get_qa()(question=question, context=context)
            score = result.get("score", 0)
            if score > 0.1:
                ans = result["answer"].strip()
                # Try to split CSV / semicolons into bullets
                if ',' in ans or ';' in ans:
                    items = re.split(r'[,;]', ans)
                    return "**Found items:**\n\n" + _bullet_format([i.strip() for i in items])
                return ans
        except Exception:
            pass
        # Fallback: extract short meaningful lines
        lines = []
        for doc in docs[:3]:
            lines.extend(_sentences(doc.page_content)[:3])
        return "**Items mentioned in the document:**\n\n" + _bullet_format(lines)

    def _answer_factual(self, question: str, docs, history_context: str = "") -> str:
        context = history_context + " ".join(d.page_content for d in docs)
        context = context[:3500]
        result = self._get_qa()(question=question, context=context)
        score = result.get("score", 0)
        answer = result["answer"].strip()
        confidence = round(score * 100, 1)
        if score < 0.05 or not answer or len(answer) < 2:
            # Fallback: return the most relevant chunk snippet
            fallback = _sentences(docs[0].page_content)
            if fallback:
                return f"{fallback[0]}\n\n*(Extracted from document — confidence low)*"
            return "I couldn't find a confident answer. Try rephrasing your question."
        return f"{answer}\n\n*(Confidence: {confidence}%)*"

    def _answer_contact(self, docs) -> str:
        patterns = {
            "Email":    r'[\w.+-]+@[\w-]+\.[a-z]{2,}',
            "Phone":    r'[\+]?[\d\s\-\(\)]{8,15}',
            "LinkedIn": r'linkedin\.com/in/[\w-]+',
            "GitHub":   r'github\.com/[\w-]+',
            "Website":  r'https?://[\w./-]+',
        }
        found = {}
        full_text = " ".join(d.page_content for d in docs)
        for label, pattern in patterns.items():
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            if matches:
                found[label] = list(dict.fromkeys(m.strip() for m in matches))[:2]
        if not found:
            return "No contact information found in the document."
        lines = [f"**{k}:** {', '.join(v)}" for k, v in found.items()]
        return "**Contact Information:**\n\n" + "\n".join(lines)

    def _answer_count(self, question: str, docs) -> str:
        context = " ".join(d.page_content for d in docs)[:3000]
        result = self._get_qa()(question=question, context=context)
        score = result.get("score", 0)
        if score > 0.05:
            return result["answer"].strip()
        # Try to count items if question is about count
        numbers = re.findall(r'\b\d+\b', context)
        if numbers:
            return f"I found numbers {', '.join(numbers[:5])} in the document. *(Confidence low — try a more specific question)*"
        return "I couldn't determine the count from the document."

    # ── Main query entry point ────────────────────────────────────────────────
    def query(self,
              question: str,
              vector_store_paths: List[str],
              chat_history: Optional[List[Tuple[str, str]]] = None) -> dict:

        if not vector_store_paths:
            return {"answer": "No documents uploaded yet. Please upload a PDF first.",
                    "sources": [], "tokens_used": 0}

        # Retrieve top chunks
        vs = self.merge_vector_stores(vector_store_paths)
        retriever = vs.as_retriever(search_type="similarity", search_kwargs={"k": 6})
        docs = retriever.invoke(question)

        # Build conversation history context (last 2 exchanges)
        history_context = ""
        if chat_history:
            recent = chat_history[-2:]
            history_context = " ".join(
                f"Q: {h[0]} A: {h[1]}" for h in recent
            ) + " "

        # Detect query type and route
        qtype = _detect_query_type(question)
        try:
            if qtype == "summary":
                answer = self._answer_summary(docs)
            elif qtype == "list":
                answer = self._answer_list(question, docs)
            elif qtype == "contact":
                answer = self._answer_contact(docs)
            elif qtype == "count":
                answer = self._answer_count(question, docs)
            else:  # factual, define, compare
                answer = self._answer_factual(question, docs, history_context)
        except Exception as e:
            logger.error(f"Query error: {e}")
            # Emergency fallback — return most relevant chunk
            answer = f"{_sentences(docs[0].page_content)[0] if docs else 'No answer found.'}\n\n*(Extracted from document)*"

        # Build citations
        sources = []
        seen = set()
        for doc in docs:
            meta = doc.metadata
            raw = meta.get("source_file", "Unknown")
            key = (raw, meta.get("page_number", ""))
            if key not in seen:
                seen.add(key)
                sources.append({
                    "file": _clean_filename(raw),
                    "page": meta.get("page_number", "?"),
                    "snippet": doc.page_content[:200].strip() + "…",
                })

        return {
            "answer": answer,
            "sources": sources,
            "tokens_used": len(question.split()) + len(answer.split()),
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
