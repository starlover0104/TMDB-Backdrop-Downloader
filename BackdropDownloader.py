import requests
from tqdm import tqdm
import sys
import os
import re

def search_media(api_key, query):
    try:
        search_url = 'https://api.themoviedb.org/3/search/multi'
        params = {'api_key': api_key, 'query': query, 'include_adult': False}

        response = requests.get(search_url, params=params)
        response.raise_for_status()

        data = response.json()
        return data.get('results', [])
    except requests.exceptions.RequestException as e:
        print(f"Error searching media: {e}")
        return []
    except ValueError as e:
        print(f"Error decoding JSON: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error during media search: {e}")
        return []

def get_tmdb_backdrops(api_key, media_id, media_type, language=None):
    try:
        base_url = f'https://api.themoviedb.org/3/{media_type}/{media_id}/images'
        params = {'api_key': api_key}

        response = requests.get(base_url, params=params)
        response.raise_for_status()

        data = response.json()
        backdrops = data.get('backdrops', [])
        
        if language:
            backdrops = [backdrop for backdrop in backdrops if backdrop.get('iso_639_1') == language]
        
        return backdrops
    except requests.exceptions.RequestException as e:
        print(f"Error getting backdrops: {e}")
        return []
    except ValueError as e:
        print(f"Error decoding JSON: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error getting backdrops: {e}")
        return []

def download_image(url, file_name):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024

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
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")
    except IOError as e:
        print(f"IOError: {e}")
    except Exception as e:
        print(f"Unexpected error during image download: {e}")

def sanitize_file_name(name):
    return re.sub(r'[(){}[\]]', '', name)

def main(api_key):
    try:
        while True:
            query = input("Enter the name of the TV show or movie (enter 'exit' to quit): ").strip()
            
            if query.lower() == 'exit':
                print("Exiting the script.")
                sys.exit(0)

            search_results = search_media(api_key, query)

            if search_results:
                while True:
                    print("\nSearch Results:")
                    for idx, result in enumerate(search_results[:5], start=1):
                        media_type = result['media_type']
                        media_type_str = "TV Show" if media_type == 'tv' else "Movie"
                        title = result.get('name', result.get('title', 'Unknown Title'))
                        release_date = result.get('first_air_date' if media_type == 'tv' else 'release_date', 'N/A')
                        print(f"{idx}. {title} [{media_type_str}] (Release Date: {release_date})")
                    print(f"{len(search_results[:5]) + 1}. Search for another TV show or movie")
                    print(f"{len(search_results[:5]) + 2}. Exit")

                    choice = input(f"\nSelect a media by number (1-{len(search_results[:5]) + 2}): ").strip()
                    if choice == str(len(search_results[:5]) + 2):
                        print("Exiting the script.")
                        sys.exit(0)
                    elif choice == str(len(search_results[:5]) + 1):
                        break
                    else:
                        try:
                            choice = int(choice)
                            if 1 <= choice <= len(search_results[:5]):
                                selected_media = search_results[choice - 1]
                                media_type = selected_media['media_type']
                                media_id = selected_media['id']
                                media_title = sanitize_file_name(selected_media.get('name', selected_media.get('title', 'Unknown Title')))

                                while True:
                                    print("\nSelect a language for backdrops:")
                                    print("1. No specific language")
                                    print("2. English")
                                    print("3. Dutch")
                                    print("4. Spanish")
                                    print("5. French")
                                    print(f"6. Go back to media selection")
                                    print(f"7. Exit")

                                    language_choice = input("\nEnter language choice (1-7): ").strip()
                                    if language_choice == '7':
                                        print("Exiting the script.")
                                        sys.exit(0)
                                    elif language_choice == '6':
                                        break
                                    else:
                                        try:
                                            language_choice = int(language_choice)
                                            languages = [None, 'en', 'nl', 'es', 'fr']

                                            if 1 <= language_choice <= len(languages):
                                                language = languages[language_choice - 1]

                                                backdrops = get_tmdb_backdrops(api_key, media_id, media_type, language=language)
                                                
                                                if backdrops:
                                                    print("\nAvailable Backdrops:")
                                                    for idx, backdrop in enumerate(backdrops, start=1):
                                                        backdrop_url = f"https://image.tmdb.org/t/p/original{backdrop['file_path']}"
                                                        print(f"{idx}. {backdrop_url}")
                                                    
                                                    while True:
                                                        backdrop_choice = input("\nSelect a backdrop by number to download (enter '0' to go back): ").strip()
                                                        if backdrop_choice == '0':
                                                            break
                                                        try:
                                                            backdrop_choice = int(backdrop_choice)
                                                            if 1 <= backdrop_choice <= len(backdrops):
                                                                selected_backdrop = backdrops[backdrop_choice - 1]
                                                                backdrop_url = f"https://image.tmdb.org/t/p/original{selected_backdrop['file_path']}"
                                                                file_name = input(f"Enter the file name for {media_title} (leave blank for default): ").strip()
                                                                if not file_name:
                                                                    file_name = f"{media_title.replace(' ', '_')}_backdrop"
                                                                    file_name = sanitize_file_name(file_name)
                                                                else:
                                                                    file_name = sanitize_file_name(file_name)
                                                                if not file_name.lower().endswith('.jpg'):
                                                                    file_name += '.jpg'
                                                                
                                                                download_image(backdrop_url, file_name)
                                                                break
                                                            else:
                                                                print("Invalid selection.")
                                                        except ValueError:
                                                            print("Invalid input. Please enter a number.")
                                                else:
                                                    print(f"No backdrops found for {language if language else 'no specific language'}.")
                                            elif language_choice == 6:
                                                break
                                            else:
                                                print("Invalid language choice.")
                                        except ValueError:
                                            print("Invalid input. Please enter a number.")
                        except ValueError:
                            print("Invalid input. Please enter a number.")
            else:
                print("No media found.")
    except KeyboardInterrupt:
        print("\nScript interrupted. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    try:
        api_key = input("Enter your TMDB API key: ").strip()
        main(api_key)
    except KeyboardInterrupt:
        print("\nScript interrupted. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
