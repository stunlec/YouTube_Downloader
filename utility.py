import yt_dlp
import streamlit as st
import tempfile
import os
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from io import BytesIO
import moviepy.editor as mp
import moviepy.editor as mp
from moviepy.video.fx.resize import resize
from io import BytesIO
import tempfile
from io import BytesIO
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import moviepy.editor as mp
from yt_dlp import YoutubeDL
import os


def get_video_info(link):
    """
    Fetch metadata and available formats for a YouTube video.
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'bestaudio/bestvideo',
        'noplaylist': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            formats = info.get('formats', [])
            all_resolutions = list({f"{fmt['width']}x{fmt['height']}" for fmt in formats if
                                    fmt.get('vcodec') != 'none' and fmt.get('width') and fmt.get('height')})

            # Determine the best resolution
            best_resolution = None
            for fmt in formats:
                if fmt.get('vcodec') != 'none':  # Ensure it's a video format
                    width = fmt.get('width', None)
                    height = fmt.get('height', None)
                    if width and height:
                        resolution = f"{width}x{height}"
                        if not best_resolution or (width * height > int(best_resolution.split('x')[0]) * int(best_resolution.split('x')[1])):
                            best_resolution = resolution

            metadata = {
                'title': info.get('title'),
                'author': info.get('uploader'),
                'duration': info.get('duration_string'),
                'description': info.get('description'),
                'formats': formats,  # Include formats for inspection
                'resolution': best_resolution or "Unknown",
                'all_resolutions': all_resolutions
            }
            return metadata
    except Exception as e:
        return {"error": str(e)}


@st.cache_resource
def download_and_clip_youtube_video(link, start_time=None, end_time=None):
    """
    Download a YouTube video, trim it between start and end times (if provided),
    and return the clip in a dictionary with video, audio, screenshots, and additional metadata.

    Args:
        link (str): The YouTube video link.
        start_time (str): Start time in MM:SS or HH:MM:SS format (can be None).
        end_time (str): End time in MM:SS or HH:MM:SS format (can be None).
        cookies_file (str): Path to the cookies file for YouTube authentication (can be None).

    Returns:
        dict: A dictionary containing the trimmed video, audio, screenshots, extension, title, subtitle, description, author, and length in milliseconds.
    """
    try:

        # Create a temporary copy of the cookies file
        # with tempfile.NamedTemporaryFile(delete=False) as tmp_cookies_file:
        #     shutil.copy(cookies_file, tmp_cookies_file.name)
        #     temp_cookies_file_path = tmp_cookies_file.name

        # Directory to store downloads
        DOWNLOAD_DIRECTORY = "downloads"
        if not os.path.exists(DOWNLOAD_DIRECTORY):
            os.makedirs(DOWNLOAD_DIRECTORY)

        # yt-dlp options with optional cookies file for authentication
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
            'outtmpl': os.path.join(DOWNLOAD_DIRECTORY, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
        }
        # ydl_opts = {
        #     'quiet': True,
        #     'no_warnings': True,
        #     # 'cookies': cookies_file if cookies_file else None,
        #     'format': 'bestaudio/bestvideo',
        #     'noplaylist': True,
        #     'outtmpl': os.path.join(DOWNLOAD_DIRECTORY, '%(title)s.%(ext)s'),
        #     'merge_output_format': 'mp4',
        # }

        # Include cookies file if provided
        # if cookies_file:
        #     ydl_opts['cookiefile'] = temp_cookies_file_path

        # Extract video information (without downloading)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            title = info_dict.get('title', 'Add Your Title')
            subtitle = info_dict.get('alt_title', 'Add Your Subtitle')
            description = info_dict.get('description', 'Add Your Description')
            author = info_dict.get('uploader', 'Unknown Author')

        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            video_title = info_dict.get('title', 'downloaded_video')
            video_filename = ydl.prepare_filename(info_dict)

        # Ensure the downloaded filename ends with .mp4
        if not video_filename.endswith('.mp4'):
            video_filename = f"Full_Video.mp4"

        # Function to convert time from HH:MM:SS or MM:SS to seconds
        def time_to_seconds(time_str):
            parts = list(map(int, time_str.split(":")))
            if len(parts) == 2:  # MM:SS
                return parts[0] * 60 + parts[1]
            elif len(parts) == 3:  # HH:MM:SS
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
            return None

        # Convert start_time and end_time to seconds
        start_second = time_to_seconds(start_time) if start_time else None
        end_second = time_to_seconds(end_time) if end_time else None

        # Clip the video if start and end times are provided
        if start_second is not None and end_second is not None:
            clipped_filename = os.path.join(DOWNLOAD_DIRECTORY, f"clipped_video.mp4")
            ffmpeg_extract_subclip(video_filename, start_second, end_second, targetname=clipped_filename)
            video_filename = clipped_filename

        # Read the video file into a BytesIO object
        video_bytes = BytesIO()
        with open(video_filename, 'rb') as video_file:
            video_bytes.write(video_file.read())

        # Reset the pointer to the beginning of the video BytesIO object
        video_bytes.seek(0)

        # Extract the audio from the video
        video_clip = mp.VideoFileClip(video_filename)
        audio_filename = os.path.join(DOWNLOAD_DIRECTORY, f"clipped_audio.mp3")
        video_clip.audio.write_audiofile(audio_filename)

        # Read the audio file into a BytesIO object
        audio_bytes = BytesIO()
        with open(audio_filename, 'rb') as audio_file:
            audio_bytes.write(audio_file.read())

        # Reset the pointer to the beginning of the audio BytesIO object
        audio_bytes.seek(0)

        # Calculate the length of the video clip in milliseconds
        length_in_milliseconds = int(video_clip.duration * 1000)

        # Generate screenshots
        # num_screenshots = 5
        # duration = video_clip.duration  # Duration of the video in seconds
        # timestamps = [duration * (i / (num_screenshots + 1)) for i in range(1, num_screenshots + 1)]
        # screenshots = []
        #
        # for i, timestamp in enumerate(timestamps):
        #     try:
        #         # Get the frame at the timestamp
        #         frame = video_clip.get_frame(timestamp)
        #
        #         # Convert frame (numpy array) to an image
        #         image = Image.fromarray(frame)
        #
        #         # Save the image to an in-memory file (BytesIO object)
        #         img_io = BytesIO()
        #         image.save(img_io, format='JPEG')
        #
        #         # Move the cursor of BytesIO to the beginning for reading
        #         img_io.seek(0)
        #
        #         # Append the in-memory image to the list
        #         screenshots.append(img_io)
        #
        #         print(f'Screenshot {i + 1} extracted at {timestamp:.2f} seconds.')
        #     except Exception as e:
        #         print(f"Error extracting screenshot {i + 1}: {e}")
        #         continue

        # Return the required dictionary
        return {
            'video': video_bytes,
            'audio': audio_bytes,
            # 'screenshots': screenshots,
            'ext': 'mp3',
            'title': title,
            'subtitle': subtitle,
            'description': description,
            'author': author,
            'length': length_in_milliseconds
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return None


# def download_and_clip_youtube_video(link, start_time=None, end_time=None):
#     """
#     Download a YouTube video, trim it between start and end times (if provided),
#     and return the clip in a dictionary with video, audio, and additional metadata.
#
#     Args:
#         link (str): The YouTube video link.
#         start_time (str): Start time in MM:SS or HH:MM:SS format (optional).
#         end_time (str): End time in MM:SS or HH:MM:SS format (optional).
#
#     Returns:
#         dict: A dictionary containing the trimmed video, audio, title, subtitle, description, author, and length in milliseconds.
#     """
#     try:
#         # yt-dlp options
#         ydl_opts = {
#             'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
#             'outtmpl': '%(title)s.%(ext)s',  # Temporary filename, will be managed in tempfile
#             'merge_output_format': 'mp4',
#         }
#
#         # Function to convert time from HH:MM:SS or MM:SS to seconds
#         def time_to_seconds(time_str):
#             parts = list(map(int, time_str.split(":")))
#             if len(parts) == 2:  # MM:SS
#                 return parts[0] * 60 + parts[1]
#             elif len(parts) == 3:  # HH:MM:SS
#                 return parts[0] * 3600 + parts[1] * 60 + parts[2]
#             return None
#
#         # Create a temporary directory
#         with tempfile.TemporaryDirectory(dir="C:\\Users\\shash\\") as temp_dir:
#             # Update yt-dlp options with the temporary directory
#             ydl_opts['outtmpl'] = os.path.join(temp_dir, '%(title)s.%(ext)s')
#
#             # Download the video
#             with YoutubeDL(ydl_opts) as ydl:
#                 info_dict = ydl.extract_info(link, download=True)
#                 video_filename = ydl.prepare_filename(info_dict)
#
#             # Ensure the downloaded filename ends with .mp4
#             if not video_filename.endswith('.mp4'):
#                 video_filename = f"{video_filename}.mp4"
#
#             # Convert start_time and end_time to seconds
#             start_second = time_to_seconds(start_time) if start_time else None
#             end_second = time_to_seconds(end_time) if end_time else None
#
#             # Clip the video if start and end times are provided
#             if start_second is not None and end_second is not None:
#                 clipped_filename = os.path.join(temp_dir, "clipped_video.mp4")
#                 ffmpeg_extract_subclip(video_filename, start_second, end_second, targetname=clipped_filename)
#                 video_filename = clipped_filename
#
#             # Read the video file into a BytesIO object
#             video_bytes = BytesIO()
#             with open(video_filename, 'rb') as video_file:
#                 video_bytes.write(video_file.read())
#
#             # Reset the pointer to the beginning of the video BytesIO object
#             video_bytes.seek(0)
#
#             # Extract the audio from the video
#             video_clip = mp.VideoFileClip(video_filename)
#             audio_filename = os.path.join(temp_dir, "clipped_audio.mp3")
#             video_clip.audio.write_audiofile(audio_filename)
#
#             # Read the audio file into a BytesIO object
#             audio_bytes = BytesIO()
#             with open(audio_filename, 'rb') as audio_file:
#                 audio_bytes.write(audio_file.read())
#
#             # Reset the pointer to the beginning of the audio BytesIO object
#             audio_bytes.seek(0)
#
#             # Calculate the length of the video clip in milliseconds
#             length_in_milliseconds = int(video_clip.duration * 1000)
#
#             # Return the required dictionary
#             return {
#                 'video': video_bytes,
#                 'audio': audio_bytes,
#                 'ext': 'mp3',
#                 'title': info_dict.get('title', 'Untitled'),
#                 'subtitle': info_dict.get('alt_title', 'No Subtitle'),
#                 'description': info_dict.get('description', 'No Description'),
#                 'author': info_dict.get('uploader', 'Unknown Author'),
#                 'length': length_in_milliseconds
#             }
#
#     except Exception as e:
#         print(f"Error: {str(e)}")
#         return None



def process_video_file(input_file: BytesIO, output_format: str, resolution: tuple = None) -> BytesIO:
    """
    Process a video file in BytesIO format and convert it to the desired format and resolution.

    Args:
        input_file (BytesIO): Input video file in BytesIO format.
        output_format (str): Desired file format (e.g., 'mp4', 'mp3', 'avi').
        resolution (tuple, optional): Desired resolution as (width, height). Only applicable for video formats.

    Returns:
        BytesIO: Processed file in the desired format as a BytesIO object.
    """
    try:
        # Save BytesIO content to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_input_file:
            temp_input_file.write(input_file.read())
            temp_input_path = temp_input_file.name
        st.write("1")
        # Load the input video from the temporary file
        video_clip = mp.VideoFileClip(temp_input_path)
        st.write("2")
        # If a resolution is provided, resize the video
        if resolution:
            video_clip = resize(video_clip, newsize=resolution)
        st.write("3")
        # Save the processed video to a temporary output file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{output_format}") as temp_output_file:
            temp_output_path = temp_output_file.name
        st.write("4")
        video_clip.write_videofile(temp_output_path, codec="libx264", audio_codec="aac")
        video_clip.close()
        st.write("5")
        # Read the processed file back into a BytesIO object
        output_bytes = BytesIO()
        with open(temp_output_path, "rb") as temp_file:
            output_bytes.write(temp_file.read())
        output_bytes.seek(0)

        # Clean up temporary files
        import os
        os.remove(temp_input_path)
        os.remove(temp_output_path)

        return output_bytes

    except Exception as e:
        print(f"Error processing video file: {e}")
        return None
