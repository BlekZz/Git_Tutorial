# YouTube Video Downloader

This script downloads YouTube videos with various quality options and includes a fallback mechanism for age-restricted or private videos using cookies.

## Prerequisites

- **Python 3.x**: Ensure you have Python installed.
- **yt-dlp**: Install with pip: `pip install -U yt-dlp`
- **ffmpeg**: Required for merging video and audio streams into a single file. Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add it to your system's PATH.
- **Node.js (LTS version)**: yt-dlp uses a JavaScript runtime to extract video information from YouTube. While the script will attempt to detect Node.js, it's highly recommended to have a modern LTS version installed and accessible in your system's PATH. You can download it from [nodejs.org](https://nodejs.org/en/download/).

## Usage

1. **Prepare `cookies.txt` (for restricted videos)**:
    Follow the instructions in the comments at the top of `script.py` to export your YouTube cookies into a `www.youtube.com_cookies.txt` file in the same directory as the script, or specify its path in a `.env` file.

2. **Run the script**:
    `python script.py`

    The script will prompt you to enter a YouTube video URL and then allow you to select a quality option.

## Debug Mode

To enable verbose logging and see more details from `yt-dlp` (including potential warnings that are normally suppressed), set the `YT_DEBUG` environment variable to `1` or `true` before running the script.

**Windows (Command Prompt):**
`set YT_DEBUG=1 && python script.py`

**Windows (PowerShell):**
`$env:YT_DEBUG="1"; python script.py`

This will help diagnose issues related to format extraction or download failures by providing more output from `yt-dlp`.
