#!/usr/bin/env python3
import os
import json
import time
import requests
from pathlib import Path
from typing import List, Set
from ddgs import DDGS

class MovieChecker:
    def __init__(self):
        self.movies_dir = os.environ.get('MOVIES_DIR', '/movies')
        self.checked_dir = os.environ.get('CHECKED_DIR', '/checked')
        self.ollama_endpoint = os.environ.get('OLLAMA_ENDPOINT', 'http://localhost:11434')
        self.ollama_model = os.environ.get('OLLAMA_MODEL', 'llama3.2')
        self.ntfy_url = os.environ.get('NTFY_URL', 'https://ntfy.sh/mytopic')
        
        print(f"Configuration:")
        print(f"  Movies directory: {self.movies_dir}")
        print(f"  Checked directory: {self.checked_dir}")
        print(f"  Ollama endpoint: {self.ollama_endpoint}")
        print(f"  Ollama model: {self.ollama_model}")
        print(f"  NTFY URL: {self.ntfy_url}")
        print()
        
        # Ensure checked directory exists
        Path(self.checked_dir).mkdir(parents=True, exist_ok=True)
    
    def get_movie_folders(self) -> List[str]:
        """Get all movie folders from the movies directory"""
        try:
            print(f"Scanning movies directory: {self.movies_dir}")
            folders = [f for f in os.listdir(self.movies_dir) 
                      if os.path.isdir(os.path.join(self.movies_dir, f))]
            print(f"Found {len(folders)} movie folders")
            return folders
        except Exception as e:
            print(f"Error scanning movies directory: {e}")
            return []
    
    def get_checked_movies(self) -> Set[str]:
        """Get set of already checked movies"""
        checked = set()
        try:
            for file in os.listdir(self.checked_dir):
                if file.endswith('.checked'):
                    checked.add(file[:-8])  # Remove .checked extension
            print(f"Found {len(checked)} already checked movies")
            return checked
        except Exception as e:
            print(f"Error reading checked directory: {e}")
            return set()
    
    def is_movie_checked(self, movie_name: str) -> bool:
        """Check if a movie has already been processed"""
        checked_file = os.path.join(self.checked_dir, f"{movie_name}.checked")
        return os.path.exists(checked_file)
    
    def mark_movie_checked(self, movie_name: str):
        """Mark a movie as checked"""
        checked_file = os.path.join(self.checked_dir, f"{movie_name}.checked")
        try:
            with open(checked_file, 'w') as f:
                f.write(str(time.time()))
            print(f"  Marked '{movie_name}' as checked")
        except Exception as e:
            print(f"  Error marking movie as checked: {e}")
    
    def ask_ollama(self, movie_name: str) -> bool:
        """Ask Ollama if the movie is Bollywood/Indian/Telugu"""
        # First, search DuckDuckGo for movie origin information
        search_query = f"{movie_name} movie country origin"
        search_results = ""
        
        try:
            print(f"  Searching DuckDuckGo for '{search_query}' with region 'us-en'...")
            with DDGS() as ddgs:
                results = list(ddgs.text(search_query, region='us-en', safesearch='off', max_results=5))
                search_results = "\n\n".join([
                    f"Result {i+1}:\nTitle: {r.get('title', 'N/A')}\nSnippet: {r.get('body', 'N/A')}\nURL: {r.get('href', 'N/A')}"
                    for i, r in enumerate(results)
                ])
            print(f"  Found {len(results)} search results")
        except Exception as e:
            print(f"  Error searching DuckDuckGo: {e}")
            search_results = "No search results available."
        
        # Now ask Ollama with the search results
        prompt = f"""Based on the following DuckDuckGo search results about the movie '{movie_name}', determine if this is a Bollywood, Indian, or Telugu speaking movie.

Search Results:
{search_results}

If the search results don't provide clear information, use your internal knowledge about the movie. If you still don't have enough information, make an educated guess based on the movie title, any patterns you recognize, or common characteristics.

Is '{movie_name}' a Bollywood, Indian, or Telugu speaking movie? Answer with just 'yes' or 'no'. No explanations, comments, nothing. Just one word: 'yes' or 'no'."""
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"  Asking Ollama about '{movie_name}' (attempt {attempt + 1}/{max_retries})...")
                print(f"\n  === PROMPT ===")
                print(f"{prompt}")
                print(f"  === END PROMPT ===\n")
                
                response = requests.post(
                    f"{self.ollama_endpoint}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    answer = result.get('response', '').strip()
                    print(f"\n  === OLLAMA RESPONSE ===")
                    print(f"{answer}")
                    print(f"  === END RESPONSE ===\n")
                    
                    answer_lower = answer.lower()
                    
                    # Check if answer contains yes or no
                    if 'yes' in answer_lower or 'no' in answer_lower:
                        decision = 'yes' if 'yes' in answer_lower else 'no'
                        print(f"  Decision: {decision}")
                        return 'yes' in answer_lower
                    else:
                        print(f"  Invalid response (no 'yes' or 'no' found): {answer}")
                        if attempt < max_retries - 1:
                            print(f"  Retrying in 5 seconds...")
                            time.sleep(5)
                            continue
                        else:
                            print(f"  Max retries reached, treating as 'no'")
                            return False
                else:
                    print(f"  Error from Ollama: {response.status_code}")
                    if attempt < max_retries - 1:
                        print(f"  Retrying in 5 seconds...")
                        time.sleep(5)
                        continue
                    else:
                        return False
                    
            except Exception as e:
                print(f"  Error asking Ollama: {e}")
                if attempt < max_retries - 1:
                    print(f"  Retrying in 5 seconds...")
                    time.sleep(5)
                    continue
                else:
                    return False
        
        return False
    
    def send_notification(self, movie_name: str):
        """Send notification to NTFY"""
        try:
            print(f"  Sending notification for '{movie_name}'...")
            response = requests.post(
                self.ntfy_url,
                data=f"Found Indian movie: {movie_name}",
                headers={
                    "Title": "New Indian Movie Found",
                    "Priority": "default",
                    "Tags": "movie,bollywood"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"  Notification sent successfully")
            else:
                print(f"  Error sending notification: {response.status_code}")
                
        except Exception as e:
            print(f"  Error sending notification: {e}")
    
    def process_movies(self):
        """Main processing loop"""
        movies = self.get_movie_folders()
        checked = self.get_checked_movies()
        
        new_movies = [m for m in movies if m not in checked]
        print(f"Found {len(new_movies)} new movies to check")
        print()
        
        for i, movie in enumerate(new_movies, 1):
            print(f"Processing movie {i}/{len(new_movies)}: '{movie}'")
            
            if self.is_movie_checked(movie):
                print(f"  Already checked, skipping")
                continue
            
            is_indian = self.ask_ollama(movie)
            
            if is_indian:
                print(f"  Identified as Indian movie")
                self.send_notification(movie)
            else:
                print(f"  Not an Indian movie")
            
            self.mark_movie_checked(movie)
            print()
            
            # Small delay to avoid overwhelming services
            time.sleep(1)
        
        print("Processing complete")

def main():
    print("Kapaladaru Movie Checker")
    print("========================")
    print()
    
    checker = MovieChecker()
    
    # Run once if RUN_ONCE is set, otherwise run continuously
    run_once = os.environ.get('RUN_ONCE', 'false').lower() == 'true'
    interval = int(os.environ.get('CHECK_INTERVAL', '3600'))  # Default 1 hour
    
    if run_once:
        print("Running in single-run mode")
        checker.process_movies()
    else:
        print(f"Running in continuous mode (interval: {interval} seconds)")
        while True:
            checker.process_movies()
            print(f"\nSleeping for {interval} seconds...")
            print("-" * 50)
            time.sleep(interval)

if __name__ == "__main__":
    main()
