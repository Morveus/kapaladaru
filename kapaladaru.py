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
        self.delete_enabled = os.environ.get('DELETE', 'false').lower() == 'true'
        self.radarr_url = os.environ.get('RADARR_URL', 'http://localhost:7878')
        self.radarr_api_key = os.environ.get('RADARR_API_KEY', '')
        
        print(f"Configuration:")
        print(f"  Movies directory: {self.movies_dir}")
        print(f"  Checked directory: {self.checked_dir}")
        print(f"  Ollama endpoint: {self.ollama_endpoint}")
        print(f"  Ollama model: {self.ollama_model}")
        print(f"  NTFY URL: {self.ntfy_url}")
        print(f"  Delete enabled: {self.delete_enabled}")
        print(f"  Radarr URL: {self.radarr_url}")
        print(f"  Radarr API key: {'*' * len(self.radarr_api_key) if self.radarr_api_key else 'Not set'}")
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
    
    def delete_from_radarr(self, movie_name: str) -> bool:
        """Delete movie from Radarr if DELETE is enabled"""
        if not self.delete_enabled:
            return False
            
        if not self.radarr_api_key:
            print(f"  Radarr API key not set, skipping deletion")
            return False
            
        try:
            print(f"  Searching for movie in Radarr: '{movie_name}'")
            
            # Search for the movie in Radarr
            search_response = requests.get(
                f"{self.radarr_url}/api/v3/movie",
                headers={"X-Api-Key": self.radarr_api_key},
                params={"term": movie_name},
                timeout=10
            )
            
            if search_response.status_code != 200:
                print(f"  Error searching Radarr: {search_response.status_code}")
                return False
                
            movies = search_response.json()
            
            # Find matching movie (case-insensitive)
            matching_movie = None
            for movie in movies:
                if movie_name.lower() in movie.get('title', '').lower():
                    matching_movie = movie
                    break
                    
            if not matching_movie:
                print(f"  Movie not found in Radarr")
                return False
                
            movie_id = matching_movie.get('id')
            movie_title = matching_movie.get('title')
            
            print(f"  Found movie in Radarr: {movie_title} (ID: {movie_id})")
            
            # Delete the movie from Radarr
            delete_response = requests.delete(
                f"{self.radarr_url}/api/v3/movie/{movie_id}",
                headers={"X-Api-Key": self.radarr_api_key},
                params={"deleteFiles": "true", "addImportExclusion": "false"},
                timeout=10
            )
            
            if delete_response.status_code in [200, 204]:
                print(f"  Successfully deleted movie from Radarr: {movie_title}")
                return True
            else:
                print(f"  Error deleting movie from Radarr: {delete_response.status_code}")
                return False
                
        except Exception as e:
            print(f"  Error deleting movie from Radarr: {e}")
            return False
    
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
                
                # Try to delete from Radarr if DELETE is enabled
                if self.delete_enabled:
                    deleted = self.delete_from_radarr(movie)
                    if deleted:
                        print(f"  Movie deleted from Radarr")
                    else:
                        print(f"  Failed to delete movie from Radarr")
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
