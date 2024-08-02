import requests, sys, os, re
from tqdm import tqdm

def get_api_key():
    try:
        with open('key.txt', 'r') as file:
            api_key = file.read().strip()
            if not api_key:
                print("Error: The 'key.txt' file is empty. Please add your TMDB API key to the file.")
                sys.exit(1)
            return api_key
    except FileNotFoundError:
        print("Error: 'key.txt' file not found in the current directory. Please create this file and add your TMDB API key to it.")
        sys.exit(1)
    except IOError as e:
        print(f"Error reading 'key.txt': {e}")
        sys.exit(1)

def check_api_key(api_key):
    try:
        url = 'https://api.themoviedb.org/3/configuration'
        params = {'api_key': api_key}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException:
        return False

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

def get_tmdb_backdrops(api_key, media_id, media_type):
    try:
        base_url = f'https://api.themoviedb.org/3/{media_type}/{media_id}/images'
        params = {'api_key': api_key, 'language': 'en'}

        response = requests.get(base_url, params=params)
        response.raise_for_status()

        data = response.json()
        backdrops = data.get('backdrops', [])
        
        # Filter for English backdrops
        english_backdrops = [b for b in backdrops if b.get('iso_639_1') == 'en' or b.get('iso_639_1') is None]
        
        return english_backdrops
    except requests.exceptions.RequestException as e:
        print(f"Error getting backdrops: {e}")
    except ValueError as e:
        print(f"Error decoding JSON: {e}")
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
        print("Make sure you have write permissions in the current directory.")
    except Exception as e:
        print(f"Unexpected error during image download: {e}")

def sanitize_file_name(name):
    sanitized = re.sub(r'[<>:"/\\|?*\[\]()]', '', name)
    return sanitized.strip()

def main():
    api_key = get_api_key()
    if not check_api_key(api_key):
        print("Error: Incorrect API key. Please check the key in your 'key.txt' file.")
        sys.exit(1)

    try:
        while True:
            query = input("Enter the name of the TV show or movie (enter 'exit' to quit): ").strip()
            
            if query.lower() == 'exit':
                print("Exiting the script.")
                sys.exit(0)

            if not query:
                print("Error: Please enter a valid search query.")
                continue

            search_results = search_media(api_key, query)

            if search_results:
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
                    continue
                else:
                    try:
                        choice = int(choice)
                        if 1 <= choice <= len(search_results[:5]):
                            selected_media = search_results[choice - 1]
                            media_type = selected_media['media_type']
                            media_id = selected_media['id']
                            media_title = sanitize_file_name(selected_media.get('name', selected_media.get('title', 'Unknown Title')))

                            backdrops = get_tmdb_backdrops(api_key, media_id, media_type)
                            
                            if backdrops:
                                print(f"\nFound {len(backdrops)} English backdrop(s) for {media_title}:")
                                for idx, backdrop in enumerate(backdrops, start=1):
                                    width = backdrop.get('width', 'N/A')
                                    height = backdrop.get('height', 'N/A')
                                    file_name = f"{media_title.replace(' ', '_')}_backdrop_{idx}.jpg"
                                    print(f"{idx}. {file_name}: Size: {width}x{height}")
                                
                                while True:
                                    backdrop_choice = input(f"\nSelect a backdrop by number (1-{len(backdrops)}): ").strip()
                                    try:
                                        backdrop_choice = int(backdrop_choice)
                                        if 1 <= backdrop_choice <= len(backdrops):
                                            selected_backdrop = backdrops[backdrop_choice - 1]
                                            backdrop_url = f"https://image.tmdb.org/t/p/original{selected_backdrop['file_path']}"
                                            
                                            file_name = f"{media_title.replace(' ', '_')}_backdrop_{backdrop_choice}"
                                            file_name = sanitize_file_name(file_name)
                                            if not file_name.lower().endswith('.jpg'):
                                                file_name += '.jpg'
                                            
                                            download_image(backdrop_url, file_name)
                                            break
                                        else:
                                            print("Invalid selection. Please choose a number from the list.")
                                    except ValueError:
                                        print("Invalid input. Please enter a number.")
                            else:
                                print(f"No English backdrops found for {media_title}.")
                        else:
                            print("Error: Invalid selection. Please choose a number from the list.")
                    except ValueError:
                        print("Error: Invalid input. Please enter a number.")
            else:
                print(f"No media found for '{query}'. Please try a different search term.")
    except KeyboardInterrupt:
        print("\nScript interrupted. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScript interrupted. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
