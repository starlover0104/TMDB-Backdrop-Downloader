import requests
from tqdm import tqdm
import os

def search_media(api_key, query):
    search_url = 'https://api.themoviedb.org/3/search/multi'
    params = {'api_key': api_key, 'query': query, 'include_adult': False}

    response = requests.get(search_url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get('results', [])
    else:
        print(f"Error: {response.status_code}")
        return []

def get_tmdb_backdrops(api_key, media_id, media_type, language=None):
    base_url = f'https://api.themoviedb.org/3/{media_type}/{media_id}/images'
    params = {'api_key': api_key}

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        backdrops = data.get('backdrops', [])
        
        if language:
            backdrops = [backdrop for backdrop in backdrops if backdrop['iso_639_1'] == language]
        
        return backdrops
    else:
        print(f"Error: {response.status_code}")
        return []

def download_image(url, file_name):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 Kibibyte

    if response.status_code == 200:
        if not file_name.lower().endswith('.jpg'):
            file_name += '.jpg'
        
        with open(file_name, 'wb') as file, tqdm(
            desc=file_name,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in response.iter_content(block_size):
                file.write(chunk)
                bar.update(len(chunk))
        print(f"\nImage downloaded: {file_name}")
    else:
        print(f"Failed to download image: {response.status_code}")

def main():
    api_key = input("Enter your TMDB API key: ").strip()
    query = input("Enter the name of the TV show or movie: ").strip()

    search_results = search_media(api_key, query)

    if search_results:
        print("\nSearch Results:")
        for idx, result in enumerate(search_results[:5], start=1):
            media_type = result['media_type']
            media_type_str = "TV Show" if media_type == 'tv' else "Movie"
            title = result.get('name', result.get('title', 'Unknown Title'))
            release_date = result.get('first_air_date' if media_type == 'tv' else 'release_date', 'N/A')
            print(f"{idx}. {title} [{media_type_str}] (Release Date: {release_date})")

        choice = int(input("\nSelect a media by number: "))
        if 1 <= choice <= len(search_results[:5]):
            selected_media = search_results[choice - 1]
            media_type = selected_media['media_type']
            media_id = selected_media['id']
            media_title = selected_media.get('name', selected_media.get('title', 'Unknown Title'))

            file_name = input(f"\nEnter the file name for {media_title}: ").strip()
            if not file_name:
                file_name = media_title.replace(' ', '_') + '_backdrop'
            
            if not file_name.lower().endswith('.jpg'):
                file_name += '.jpg'

            while True:
                print("\nSelect a language for backdrops:")
                print("1. No specific language")
                print("2. Dutch")
                print("3. English")
                print("4. Spanish")
                print("5. French")
                
                language_choice = int(input("\nEnter language choice (1-5): "))
                languages = [None, 'nl', 'en', 'es', 'fr']
                
                if 1 <= language_choice <= len(languages):
                    language = languages[language_choice - 1]

                    backdrops = get_tmdb_backdrops(api_key, media_id, media_type, language=language)
                    
                    if backdrops:
                        print("\nAvailable Backdrops:")
                        for idx, backdrop in enumerate(backdrops, start=1):
                            backdrop_url = f"https://image.tmdb.org/t/p/original{backdrop['file_path']}"
                            print(f"{idx}. {backdrop_url}")
                        
                        backdrop_choice = int(input("\nSelect a backdrop by number to download: "))
                        if 1 <= backdrop_choice <= len(backdrops):
                            selected_backdrop = backdrops[backdrop_choice - 1]
                            backdrop_url = f"https://image.tmdb.org/t/p/original{selected_backdrop['file_path']}"
                            
                            download_image(backdrop_url, file_name)
                        else:
                            print("Invalid selection.")
                    else:
                        print(f"No backdrops found for {language if language else 'no specific language'}.")
                        continue
                else:
                    print("Invalid language choice.")
                
                retry_choice = input("\nDo you want to try another language? (yes/no): ").strip().lower()
                if retry_choice != 'yes':
                    break 
        else:
            print("Invalid selection.")
    else:
        print("No media found.")
    
    restart_choice = input("\nDo you want to search for another TV show or movie? (yes/no): ").strip().lower()
    if restart_choice == 'yes':
        main()

if __name__ == "__main__":
    main()
