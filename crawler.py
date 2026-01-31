# Importing Libraries
import requests
from neo4j import GraphDatabase
import time
import pandas as pd
import json
import os


# from dotenv import load_dotenv
# import os

# load_dotenv()
# neo4j_uri = os.getenv("NEO4J_URI")
# neo4j_user = os.getenv("NEO4J_USER")
# neo4j_password = os.getenv("NEO4J_PASSWORD")
# neo4j_db = os.getenv("NEO4J_DB")


# Config values
neo4j_uri = "xxxxxxx"
neo4j_user = "xxxxxxx"
neo4j_password = "xxxxxxx"
neo4j_db = "xxxxxxx"

driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

wiki_url = "https://en.wikipedia.org/w/api.php"

visited_file = "visited.json"
queue_file = "queue.json"


# Read initial values from files
def load_state(start_page):
    if os.path.exists(visited_file):
        with open(visited_file, "r") as f:
            visited = set(json.load(f))
    else:
        visited = set()

    if os.path.exists(queue_file):
        with open(queue_file, "r") as f:
            queue = json.load(f)
    else:
        queue = [start_page]

    queue_set = set(queue)
    return visited, queue, queue_set
    

# Save data to files
def save_state(visited, queue):
    with open(visited_file, "w") as f:
        json.dump(list(visited), f)

    with open(queue_file, "w") as f:
        json.dump(queue, f)


# Saving to Neo4j
def save_page_links(tx, page, page_id, links):
    query = """
    MERGE (p:Page {title: $page})
    ON CREATE SET p.page_id = $page_id
    ON MATCH SET p.page_id = coalesce(p.page_id, $page_id)
    WITH p
    UNWIND $links AS l
        MERGE (l_page:Page {title: l})
        MERGE (p)-[:HAS_LINK]->(l_page)
    """
    tx.run(query, page=page, page_id=page_id, links=links)
    

# Get Links from Wikipedia
def get_links(page_title):
    plcontinue = None
    link_list = []
    
    while True:
        params = {
            "action": "query",
            "format": "json",
            "titles": page_title,
            "prop": "links",
            "pllimit": "max"
        }
    
        if plcontinue:
            params["plcontinue"] = plcontinue
    
        headers = {"User-Agent": "MyWikiCrawler/1.0 (https://yourwebsite.com; email@example.com)"}
    
        time.sleep(0.1)
        response = requests.get(WIKI_API, params=params, headers=headers)
        if response.status_code != 200:
            print(f"Error fetching page: {page_title}")
            break
    
        data = response.json()
        pages = data["query"]["pages"]
        for page_id, page_data in pages.items():
            if "links" in page_data:
                link_frame = pd.DataFrame(page_data["links"])
                link_list.append(link_frame)
    
        if "continue" in data and "plcontinue" in data["continue"]:
            plcontinue = data["continue"]["plcontinue"]
        else:
            break
    
    final_frame= pd.concat(link_list)
    links = list(set(final_frame[final_frame['ns'] == 0]['title']))

    return page_id, links
    
    
# Crawl Wikipedia
def crawl_wikipedia(start_page, max_pages=1000, save_every=5):
    visited, queue, queue_set = load_state(start_page)
    print(f"Loaded {len(visited)} visited pages and {len(queue)} pages in queue.")

    with driver.session(database=neo4j_db) as session:
        processed_since_save = 0

        while queue and len(visited) < max_pages:
            current_page = queue.pop(0)

            if current_page in visited:
                continue

            print(f"Crawling: {current_page} ({len(visited)+1}/{max_pages})")
            
            try:
                page_id, links = get_links(current_page)
                visited.add(current_page)
                queue_set.remove(current_page)
            except Exception as e:
                print(f"Error getting links for {current_page}: {e}")
                continue

            session.execute_write(save_page_links, current_page, page_id, links)

            for link in links:
                if link not in visited:
                    queue.append(link)
                    queue_set.add(link)

            processed_since_save += 1

            # Save progress periodically
            if processed_since_save >= save_every:
                save_state(visited, queue)
                processed_since_save = 0
                print("Progress saved.")

            time.sleep(0.1)

    # Final save when stopping
    save_state(visited, queue)
    print("Final progress saved.")


if __name__ == "__main__":
    start_page = "Hydrogen"
    max_pages = 1000

    crawl_wikipedia(start_page, max_pages)
    print("Crawling session complete!")