import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import sqlite3
import hashlib

class WebCrawler:
    def __init__(self, db_path='search_index.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                title TEXT,
                content TEXT,
                description TEXT,
                last_crawled TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS index (
                word TEXT,
                page_id INTEGER,
                frequency INTEGER,
                positions TEXT,
                FOREIGN KEY(page_id) REFERENCES pages(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_page_hash(self, content):
        return hashlib.md5(content.encode()).hexdigest()
    
    def extract_text(self, soup):
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        return soup.get_text()
    
    def crawl(self, url, max_pages=100):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        visited = set()
        to_visit = [url]
        
        while to_visit and len(visited) < max_pages:
            current_url = to_visit.pop(0)
            
            if current_url in visited:
                continue
                
            try:
                print(f"Crawling: {current_url}")
                response = requests.get(current_url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract page information
                title = soup.title.string if soup.title else ''
                content = self.extract_text(soup)
                description = ''
                
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc:
                    description = meta_desc.get('content', '')
                
                # Insert or update page
                c.execute('''
                    INSERT OR REPLACE INTO pages (url, title, content, description)
                    VALUES (?, ?, ?, ?)
                ''', (current_url, title, content, description))
                
                page_id = c.lastrowid
                
                # Index content
                self.index_page(c, page_id, content)
                
                conn.commit()
                visited.add(current_url)
                
                # Extract links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(current_url, href)
                    
                    if (urlparse(full_url).netloc == urlparse(url).netloc and 
                        full_url not in visited and 
                        full_url not in to_visit):
                        to_visit.append(full_url)
                
                time.sleep(1)  # Be polite
                
            except Exception as e:
                print(f"Error crawling {current_url}: {e}")
                continue
        
        conn.close()
        return len(visited)
    
    def index_page(self, cursor, page_id, content):
        # Simple word tokenization and frequency counting
        words = content.lower().split()
        word_positions = {}
        
        for position, word in enumerate(words):
            if word not in word_positions:
                word_positions[word] = []
            word_positions[word].append(position)
        
        for word, positions in word_positions.items():
            if len(word) > 2:  # Ignore very short words
                cursor.execute('''
                    INSERT INTO index (word, page_id, frequency, positions)
                    VALUES (?, ?, ?, ?)
                ''', (word, page_id, len(positions), str(positions)))
