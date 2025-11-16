import sqlite3
import time
import math
from urllib.parse import urlparse

class SearchEngine:
    def __init__(self, db_path='search_index.db'):
        self.db_path = db_path
        self.results_per_page = 10
    
    def search(self, query, page=1):
        start_time = time.time()
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Simple search using SQL LIKE (for demo purposes)
        # In production, you'd use full-text search or more sophisticated matching
        query_terms = query.lower().split()
        
        # Build search conditions
        conditions = []
        params = []
        
        for term in query_terms:
            conditions.append("(p.title LIKE ? OR p.content LIKE ? OR p.description LIKE ?)")
            params.extend([f'%{term}%', f'%{term}%', f'%{term}%'])
        
        where_clause = " OR ".join(conditions)
        
        # Get total count
        c.execute(f'''
            SELECT COUNT(DISTINCT p.id) 
            FROM pages p
            WHERE {where_clause}
        ''', params)
        
        total_results = c.fetchone()[0]
        
        # Calculate pagination
        offset = (page - 1) * self.results_per_page
        
        # Get results for current page
        c.execute(f'''
            SELECT p.url, p.title, p.description, 
                   p.content,
                   (
                       (CASE WHEN p.title LIKE ? THEN 3 ELSE 0 END) +
                       (CASE WHEN p.description LIKE ? THEN 2 ELSE 0 END) +
                       (CASE WHEN p.content LIKE ? THEN 1 ELSE 0 END)
                   ) as relevance
            FROM pages p
            WHERE {where_clause}
            ORDER BY relevance DESC, p.last_crawled DESC
            LIMIT ? OFFSET ?
        ''', params + [f'%{query}%', f'%{query}%', f'%{query}%', self.results_per_page, offset])
        
        results = []
        for row in c.fetchall():
            url, title, description, content, relevance = row
            
            # Generate snippet
            snippet = self.generate_snippet(content, query_terms)
            
            results.append({
                'url': url,
                'title': title or 'No title',
                'snippet': snippet,
                'display_url': self.get_display_url(url)
            })
        
        conn.close()
        
        search_time = time.time() - start_time
        
        return results, total_results, search_time
    
    def generate_snippet(self, content, query_terms, max_length=160):
        """Generate a text snippet highlighting search terms"""
        content_lower = content.lower()
        
        # Find the best position with most query terms
        best_pos = -1
        max_terms = 0
        
        for i in range(0, min(len(content), 1000), 100):
            segment = content_lower[i:i+200]
            term_count = sum(1 for term in query_terms if term in segment)
            
            if term_count > max_terms:
                max_terms = term_count
                best_pos = i
        
        if best_pos == -1:
            best_pos = 0
        
        # Extract snippet
        snippet = content[best_pos:best_pos + max_length]
        
        if best_pos + max_length < len(content):
            snippet += "..."
        
        # Highlight query terms (simple version)
        for term in query_terms:
            snippet = snippet.replace(term, f"<strong>{term}</strong>")
            snippet = snippet.replace(term.capitalize(), f"<strong>{term.capitalize()}</strong>")
        
        return snippet
    
    def get_display_url(self, url):
        """Convert URL to display format"""
        parsed = urlparse(url)
        return parsed.netloc + parsed.path
