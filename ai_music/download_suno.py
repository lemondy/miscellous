import requests
from mutagen.mp3 import MP3
import os
import re
from bs4 import BeautifulSoup
import gradio as gr

def extract_media_urls(suno_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(suno_url, headers=headers)
    print(response.status_code)
    # print(response.text)
    # response.text write to file
    with open('response.txt', 'w') as f:
        f.write(response.text)
    
        # Extract the title from the HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.title.string if soup.title else "No title found"
    title_array = [title]  # Store the title in an array
    print('title:', title)
    # Use regex to find all MP3 URLs
    media_urls = re.findall(r'https?://[^\s,"]+\.mp3', response.text)
    
    # Optionally, you can also look for MP4 URLs if needed
    # media_urls += re.findall(r'https?://[^\s,"]+\.mp4', response.text)
    # Filter out any duplicates and ensure clean URLs
    media_urls = list(set(media_urls))  # Remove duplicates

    for url in media_urls:
        print('url:', url)  # Print the extracted URLs for debugging

    return media_urls,title_array

def download_media(urls, music_directory, title_array):
    if not os.path.exists(music_directory):
        os.makedirs(music_directory)
    
    saved_file_paths = []  # List to store the paths of downloaded files
    with open(os.path.join(music_directory, 'media_urls.txt'), 'w') as f:
        for url in urls:
            f.write(url + '\n')
            response = requests.get(url)
            filename = os.path.join(music_directory, os.path.basename(url))
            
            # Check if the file is an MP3
            if url.endswith('.mp3'):
                # Save the temporary file to check its duration
                with open(filename, 'wb') as media_file:
                    media_file.write(response.content)
                
                # Check the duration of the MP3 file
                audio = MP3(filename)
                duration = audio.info.length
                
                if duration < 20:
                    print(f"Skipping download of {url}: duration {duration:.2f} seconds is less than 20 seconds.")
                    os.remove(filename)  # Remove the temporary file
                else:
                    print(f"Downloaded: {url} (Duration: {duration:.2f} seconds)")
                    saved_file_paths.append(filename)  # Add the saved file path to the list
            else:
                with open(filename, 'wb') as media_file:
                    media_file.write(response.content)
                    saved_file_paths.append(filename)  # Add the saved file path to the list

    return saved_file_paths  # Return the list of saved file paths


def process_urls(urls):
    all_results = []
    for url in urls.splitlines():  # Split input by new lines for multiple URLs
        media_urls, title_array = extract_media_urls(url)
        saved_file_paths = download_media(media_urls, 'music', title_array)
        # Append results for each URL
        for title, path in zip(title_array, saved_file_paths):
            all_results.append({"Title": title, "MP3 Path": path})
    
    # Convert the list of dictionaries to a list of tuples for Gradio
    return [(result["Title"], result["MP3 Path"]) for result in all_results] if all_results else [("No results", "")]


def rename_mp3(dataframe):
    results = []
    for index, row in dataframe.iterrows():
        title = row["Title"]
        mp3_path = row["MP3 Path"]
        
        # Extract the directory and new filename
        directory = os.path.dirname(mp3_path)
        new_filename = os.path.join(directory, f"{title}.mp3")
        
        # Rename the file
        try:
            os.rename(mp3_path, new_filename)
            results.append(f"Renamed {mp3_path} to {new_filename}")
        except Exception as e:
            results.append(f"Error renaming {mp3_path}: {str(e)}")
    
    return results  # Return the results of the renaming operation

if __name__ == "__main__":
    with gr.Blocks() as iface:
        gr.Markdown("### Suno URL Media Downloader")
        gr.Markdown("Input multiple Suno URLs to extract media and download MP3 files.")
        
        # Input component
        url_input = gr.Textbox(lines=5, placeholder="Enter multiple URLs, one per line...")
        
        # Buttons in a horizontal layout
        with gr.Row():
            clear_button = gr.ClearButton()
            submit_button = gr.Button("Submit", elem_id="submit-button")  # Highlighted button
            
        # Output component
        output_table = gr.Dataframe(headers=["Title", "MP3 Path"])  # Keep paths as strings
        
        # Define the interaction
        submit_button.click(fn=process_urls, inputs=url_input, outputs=output_table)
        clear_button.click(fn=lambda: "", inputs=[], outputs=url_input)  # Clear the input box
        
        # Add button for renaming MP3 files
        rename_button = gr.Button("Rename MP3 Files")
        
        # New output component for renaming messages
        rename_output = gr.Textbox(label="Renaming Messages", interactive=False)
        
        rename_button.click(fn=rename_mp3, inputs=output_table, outputs=rename_output)  # Output to the new textbox

        # Add custom CSS for the submit button
        gr.Markdown("""
        <style>
        #submit-button {
            background-color: orange; /* Orange background */
            color: white; /* White text */
            border: none; /* No border */
            padding: 10px 20px; /* Some padding */
            text-align: center; /* Centered text */
            text-decoration: none; /* No underline */
            display: inline-block; /* Inline-block */
            font-size: 16px; /* Larger font size */
            margin: 4px 2px; /* Margin around the button */
            cursor: pointer; /* Pointer cursor on hover */
        }
        #submit-button:hover {
            background-color: darkorange; /* Darker orange on hover */
        }
        </style>
        """)

    iface.launch()