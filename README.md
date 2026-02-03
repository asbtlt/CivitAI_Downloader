# CivitAI Downloader

A command-line tool for downloading models from CivitAI with resume support.

## Features

- 🚀 Download models from CivitAI using API
- ⏸️ Resume interrupted downloads
- 🔐 Secure API token storage
- 📊 Real-time download progress with speed indicator
- 🎯 Simple command-line interface

## Installation

### From PyPI (after publishing)

```bash
pip install civitai-downloader
```

### From source

```bash
git clone https://github.com/asbtlt/civitai-downloader.git
cd civitai-downloader
pip install .
```

### Development installation

```bash
pip install -e .
```

## Usage

After installation, you can use the `civitai-dl` command:

```bash
# Download to current directory
civitai-dl https://civitai.com/api/download/models/46846

# Download to specific directory
civitai-dl https://civitai.com/api/download/models/46846 /path/to/output

# First time usage - you'll be prompted for your CivitAI API token
```

## Getting your CivitAI API token

1. Go to <https://civitai.com>
2. Login to your account
3. Go to Account Settings > API Keys
4. Create a new API key
5. The token will be securely stored in `~/.civitai/config`

## Requirements

- Python 3.7+
- No external dependencies (uses only standard library)

## License

MIT License
