"""SQLite database with FTS5 full-text search for the vertical slice."""
import sqlite3
from typing import List, Optional, Dict, Any
from pathlib import Path

from backend.core.logging import get_logger
from backend.core.models import Manuscript, SearchResult, BoundingBox
from backend.core.exceptions import IndexingException, SearchException

logger = get_logger(__name__)


class Database:
    """SQLite database with FTS5 for full-text search."""

    def __init__(self, db_path: str = "olaisearch.db"):
        """Initialize database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        logger.info("database_initialized", db_path=db_path)

    def connect(self) -> None:
        """Create database connection and initialize schema."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        self._init_schema()
        logger.info("database_connected")

    def _init_schema(self) -> None:
        """Create tables if they don't exist."""
        if not self.conn:
            raise IndexingException("Database not connected")

        cursor = self.conn.cursor()

        # Manuscripts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS manuscripts (
                id TEXT PRIMARY KEY,
                image_path TEXT NOT NULL,
                restored_image_path TEXT,
                language TEXT NOT NULL,
                script TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Lines table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lines (
                id TEXT PRIMARY KEY,
                manuscript_id TEXT NOT NULL,
                text TEXT NOT NULL,
                bbox_x INTEGER,
                bbox_y INTEGER,
                bbox_width INTEGER,
                bbox_height INTEGER,
                confidence REAL,
                script TEXT,
                line_number INTEGER,
                FOREIGN KEY (manuscript_id) REFERENCES manuscripts(id)
            )
        """)

        # FTS5 virtual table for full-text search
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS lines_fts USING fts5(
                line_id UNINDEXED,
                manuscript_id UNINDEXED,
                text,
                tokenize='unicode61'
            )
        """)

        self.conn.commit()
        logger.info("database_schema_initialized")

    def index_manuscript(self, manuscript: Manuscript) -> None:
        """Index a manuscript and its lines.

        Args:
            manuscript: Manuscript to index

        Raises:
            IndexingException: If indexing fails
        """
        if not self.conn:
            raise IndexingException("Database not connected")

        try:
            cursor = self.conn.cursor()

            # Insert manuscript
            cursor.execute("""
                INSERT OR REPLACE INTO manuscripts
                (id, image_path, restored_image_path, language, script, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                manuscript.id,
                manuscript.image_path,
                manuscript.restored_image_path,
                manuscript.language,
                manuscript.script,
                str(manuscript.metadata)
            ))

            # Insert lines
            for idx, line in enumerate(manuscript.lines):
                cursor.execute("""
                    INSERT OR REPLACE INTO lines
                    (id, manuscript_id, text, bbox_x, bbox_y, bbox_width, bbox_height,
                     confidence, script, line_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    line.id,
                    manuscript.id,
                    line.text,
                    line.bbox.x,
                    line.bbox.y,
                    line.bbox.width,
                    line.bbox.height,
                    line.confidence,
                    line.script,
                    idx
                ))

                # Index in FTS5
                cursor.execute("""
                    INSERT OR REPLACE INTO lines_fts (line_id, manuscript_id, text)
                    VALUES (?, ?, ?)
                """, (line.id, manuscript.id, line.text))

            self.conn.commit()
            logger.info(
                "manuscript_indexed",
                manuscript_id=manuscript.id,
                num_lines=len(manuscript.lines)
            )

        except Exception as e:
            self.conn.rollback()
            logger.error("indexing_error", manuscript_id=manuscript.id, error=str(e))
            raise IndexingException(f"Failed to index manuscript: {str(e)}") from e

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search for text using BM25 via FTS5.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of search results ranked by BM25 score

        Raises:
            SearchException: If search fails
        """
        if not self.conn:
            raise SearchException("Database not connected")

        try:
            cursor = self.conn.cursor()

            # BM25 search using FTS5
            cursor.execute("""
                SELECT
                    l.id as line_id,
                    l.manuscript_id,
                    l.text,
                    l.bbox_x,
                    l.bbox_y,
                    l.bbox_width,
                    l.bbox_height,
                    l.confidence,
                    l.script,
                    fts.rank as score
                FROM lines_fts fts
                JOIN lines l ON fts.line_id = l.id
                WHERE lines_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit))

            results = []
            for row in cursor.fetchall():
                results.append(SearchResult(
                    manuscript_id=row['manuscript_id'],
                    line_id=row['line_id'],
                    text=row['text'],
                    score=abs(row['score']),  # FTS5 rank is negative
                    bbox=BoundingBox(
                        x=row['bbox_x'],
                        y=row['bbox_y'],
                        width=row['bbox_width'],
                        height=row['bbox_height']
                    ),
                    metadata={
                        'confidence': row['confidence'],
                        'script': row['script']
                    }
                ))

            logger.info(
                "search_success",
                query=query,
                num_results=len(results)
            )

            return results

        except Exception as e:
            logger.error("search_error", query=query, error=str(e))
            raise SearchException(f"Search failed: {str(e)}") from e

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("database_closed")
