#!/usr/bin/env python3

import os.path
import sys
import argparse
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote


CHUNK_SIZE = 1638400
TOKEN_FILE = Path.home() / '.civitai' / 'config'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
BASE_URL = 'https://civitai.com/api/download/models/'


def normalize_url(url_or_id: str) -> str:
    """Convert model ID to full URL if needed."""
    # If it's just a number, add the base URL
    if url_or_id.isdigit():
        return BASE_URL + url_or_id
    # If it already starts with http, return as is
    if url_or_id.startswith('http'):
        return url_or_id
    # Otherwise assume it's an ID and add base URL
    return BASE_URL + url_or_id


def get_args():
    parser = argparse.ArgumentParser(
        description='CivitAI Downloader',
    )

    parser.add_argument(
        'url',
        type=str,
        help='Model ID or full URL, eg: 46846 or https://civitai.com/api/download/models/46846'
    )

    parser.add_argument(
        'output_path',
        type=str,
        nargs='?',
        default='.',
        help='Output path, eg: /workspace/stable-diffusion-webui/models/Stable-diffusion (default: current directory)'
    )

    return parser.parse_args()


def get_token():
    try:
        with open(TOKEN_FILE, 'r', encoding='utf-8') as file:
            token = file.read()
            return token
    except (FileNotFoundError, IOError):
        return None


def store_token(token: str):
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(TOKEN_FILE, 'w', encoding='utf-8') as file:
        file.write(token)


def prompt_for_civitai_token():
    token = input('Please enter your CivitAI API token: ')
    store_token(token)
    return token


def download_file(url: str, output_path: str, token: str):
    headers = {
        'Authorization': f'Bearer {token}',
        'User-Agent': USER_AGENT,
    }

    # Disable automatic redirect handling
    class NoRedirection(urllib.request.HTTPErrorProcessor):
        def http_response(self, request, response):
            return response
        https_response = http_response

    request = urllib.request.Request(url, headers=headers)
    opener = urllib.request.build_opener(NoRedirection)
    response = opener.open(request)

    if response.status in [301, 302, 303, 307, 308]:
        redirect_url = response.getheader('Location')

        # Extract filename from the redirect URL
        parsed_url = urlparse(redirect_url)
        query_params = parse_qs(parsed_url.query)
        content_disposition = query_params.get('response-content-disposition', [None])[0]

        if content_disposition:
            filename = unquote(content_disposition.split('filename=')[1].strip('"'))
        else:
            raise ValueError('Unable to determine filename')
    elif response.status == 404:
        raise FileNotFoundError('File not found')
    else:
        raise RuntimeError('No redirect found, something went wrong')

    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    
    output_file = os.path.join(output_path, filename)
    
    # Check if file already exists (for resume)
    resume_byte_pos = 0
    if os.path.exists(output_file):
        resume_byte_pos = os.path.getsize(output_file)
        print(f'Found existing file, resuming from {resume_byte_pos / (1024**2):.2f} MB')
    
    # Add Range header for resume functionality
    if resume_byte_pos > 0:
        resume_headers = {'Range': f'bytes={resume_byte_pos}-'}
        resume_request = urllib.request.Request(redirect_url, headers=resume_headers)
        response = urllib.request.urlopen(resume_request)
        
        # Check if server supports range requests
        if response.status == 206:  # Partial Content
            print('Server supports resume, continuing download...')
        elif response.status == 200:  # Server doesn't support range, restart
            print('Server does not support resume, restarting download...')
            resume_byte_pos = 0
            response = urllib.request.urlopen(redirect_url)
        else:
            raise RuntimeError(f'Unexpected response status: {response.status}')
    else:
        response = urllib.request.urlopen(redirect_url)

    total_size = response.getheader('Content-Length')

    if total_size is not None:
        total_size = int(total_size)
        if resume_byte_pos > 0 and response.status == 206:
            # For partial content, add the already downloaded size
            total_size += resume_byte_pos

    # Open file in append mode if resuming, otherwise write mode
    file_mode = 'ab' if resume_byte_pos > 0 else 'wb'
    with open(output_file, file_mode) as f:
        downloaded = resume_byte_pos
        start_time = time.time()
        speed = 0

        while True:
            chunk_start_time = time.time()
            buffer = response.read(CHUNK_SIZE)
            chunk_end_time = time.time()

            if not buffer:
                break

            downloaded += len(buffer)
            f.write(buffer)
            chunk_time = chunk_end_time - chunk_start_time

            if chunk_time > 0:
                speed = len(buffer) / chunk_time / (1024 ** 2)  # Speed in MB/s

            if total_size is not None:
                progress = downloaded / total_size
                sys.stdout.write(f'\rDownloading: {filename} [{progress*100:.2f}%] - {speed:.2f} MB/s')
                sys.stdout.flush()

    end_time = time.time()
    time_taken = end_time - start_time
    hours, remainder = divmod(time_taken, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        time_str = f'{int(hours)}h {int(minutes)}m {int(seconds)}s'
    elif minutes > 0:
        time_str = f'{int(minutes)}m {int(seconds)}s'
    else:
        time_str = f'{int(seconds)}s'

    sys.stdout.write('\n')
    print(f'Download completed. File saved as: {filename}')
    print(f'Downloaded in {time_str}')


def main():
    args = get_args()
    token = get_token()

    if not token:
        token = prompt_for_civitai_token()

    # Normalize URL (convert ID to full URL if needed)
    url = normalize_url(args.url)

    try:
        download_file(url, args.output_path, token)
    except (ValueError, FileNotFoundError, RuntimeError, IOError, urllib.error.URLError) as e:
        print(f'ERROR: {e}')


if __name__ == '__main__':
    main()
