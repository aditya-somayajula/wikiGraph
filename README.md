# Wikipedia Neo4j Crawler

This project is a **Python crawler** that builds a **graph database of Wikipedia pages** in **Neo4j**.  

- Each Wikipedia page is stored as a `Page` node with its `title` (and optionally `page_id`).  
- Links between pages are stored as `HAS_LINK` relationships.  
- The crawler supports **resumable crawling**, avoiding duplicate nodes and queue entries.  

It’s ideal for exploring Wikipedia’s link structure or experimenting with graph algorithms locally.

---

## Features

- Crawl Wikipedia pages starting from a given page.
- Extract all links on a page.
- Store pages as nodes (`Page`) and links as relationships (`HAS_LINK`) in Neo4j.
- **Resumable**: saves visited pages and queue in JSON files (`visited.json` and `queue.json`).
- Avoids duplicates in nodes and queue.
- Polite API usage with a custom `User-Agent`.
- Fully compatible with **Neo4j Desktop** or any local Neo4j instance.

---

## Project Structure

```
wiki-neo4j-crawler/
│
├─ crawler.py          # Main Python crawler script
├─ requirements.txt    # Python dependencies
├─ README.md           # Project documentation
├─ .gitignore          # Ignore cache and JSON files
├─ visited.json        # Auto-generated: pages already crawled
├─ queue.json          # Auto-generated: pages waiting to be crawled
```

**Note:** `visited.json` and `queue.json` are automatically generated and should **not** be tracked in Git (`.gitignore` included).

---

## Prerequisites

1. **Python 3.9+**
2. **Neo4j Desktop or Server** installed locally
3. Python libraries:

```bash
pip install -r requirements.txt
```

`requirements.txt` includes:

```
requests
neo4j
python-dotenv   # optional if using .env for credentials
```

---

## Configuration

### Neo4j Setup

- Ensure Neo4j Desktop is running.
- Create a database (e.g., `neo4j`) and note credentials:

```
URI: bolt://localhost:7687
User: neo4j
Password: <your_password>
```

- Optional: Create a uniqueness constraint to improve performance:

```cypher
CREATE CONSTRAINT page_title_unique IF NOT EXISTS
FOR (p:Page) REQUIRE p.title IS UNIQUE;
```

### Environment Variables (Recommended)

Create a `.env` file to avoid hardcoding passwords:

```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DB=neo4j
```

In `crawler.py`:

```python
from dotenv import load_dotenv
import os

load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DB = os.getenv("NEO4J_DB")
```

---

## Running the Crawler

```bash
python crawler.py
```

Default settings in `crawler.py`:

```python
START_PAGE = "Hydrogen"
MAX_PAGES = 5000
```

- **START_PAGE**: initial page for the crawl (only used if queue file is empty).  
- **MAX_PAGES**: maximum number of pages to crawl in this session.  

The crawler will automatically **resume from `visited.json` and `queue.json`** if the process is restarted.

---

## Resuming a Crawl

1. Do **not delete** `visited.json` or `queue.json`.
2. Run `crawler.py` again.
3. The crawler will pick up where it left off automatically.

---

## Queries to Explore the Graph

Once data is in Neo4j, you can explore:

**Count nodes and relationships**

```cypher
MATCH (p:Page) RETURN count(p);
MATCH ()-[r:HAS_LINK]->() RETURN count(r);
```

**Top linked pages**

```cypher
MATCH (p:Page)<-[:HAS_LINK]-()
RETURN p.title, count(*) AS in_degree
ORDER BY in_degree DESC
LIMIT 10;
```

**Visualize a small subgraph**

```cypher
MATCH (p:Page)-[:HAS_LINK]->(q:Page)
RETURN p, q
LIMIT 50;
```

---

## Polite Crawling

- The crawler uses a **custom User-Agent** to comply with Wikipedia’s API guidelines.
- Requests are throttled (`time.sleep`) to avoid overloading servers.
- Always respect Wikipedia's [robots policy](https://www.mediawiki.org/wiki/Manual:Bot_policy).

---

## Notes / Tips

- JSON queue storage works well for small to medium crawls. For very large crawls (hundreds of thousands of pages), consider using **SQLite** or another persistent queue backend.
- Batch writes to Neo4j are important if the graph grows beyond tens of thousands of nodes to maintain speed.
- You can safely stop the crawler anytime; progress is automatically saved.

---

## License

This project is released under the **MIT License**. Feel free to modify and redistribute.

---

## References

- [Wikipedia API Documentation](https://www.mediawiki.org/wiki/API:Main_page)  
- [Neo4j Python Driver](https://neo4j.com/docs/api/python-driver/current/)  
- [Neo4j Desktop](https://neo4j.com/download/)

