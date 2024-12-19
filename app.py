import streamlit as st
import utility

session_keys = ['step_1', 'step_2', 'step_3', 'step_4', 'video_info', 'start_time', 'end_time', 'video_file',
                'format_option', 'processed_file']

for key in session_keys:
    if key not in st.session_state:
        if key == 'step_1':
            st.session_state['step_1'] = True
        elif key == 'step_2':
            st.session_state['step_2'] = False
        elif key == 'step_3':
            st.session_state['step_3'] = False
        elif key == 'step_4':
            st.session_state['step_4'] = False
        else:
            st.session_state[key] = None

st.title('YouTube Video/Audio Downloader 🎥🎵')

if st.session_state['step_1']:
    with st.form('first_step'):
        st.header("Provide YouTube Video Link")
        youtube_link = st.text_input("Paste the YouTube link here:")
        start_time = st.text_input("Start Time (MM:SS or HH:MM:SS, optional):", placeholder="e.g., 00:10")
        end_time = st.text_input("End Time (MM:SS or HH:MM:SS, optional):", placeholder="e.g., 01:00")

        if st.form_submit_button('Fetch Video Details'):
            if not youtube_link:
                st.warning("Please enter YouTube Link!")
            else:
                with st.spinner("Fetching the details..."):
                    try:
                        video_info = utility.get_video_info(youtube_link)
                        if video_info is None:
                            st.error("An error occurred while fetching the video details")
                        else:
                            st.session_state['video_info'] = video_info
                            st.session_state['start_time'] = start_time
                            st.session_state['end_time'] = end_time
                            st.session_state['step_2'] = True
                            st.rerun()
                    except Exception as e:
                        st.error(f"An error occurred: {e}")

if st.session_state['step_2']:
    with st.form('second_step'):
        st.header("Video Details")
        st.write(f"**Title:** {st.session_state.video_info['title']}")
        st.write(f"**Author:** {st.session_state.video_info['author']}")
        st.write(f"**Duration:** {st.session_state.video_info['duration']}")
        st.write(f"**Resolution:** {st.session_state.video_info['resolution']}")
        # st.write(f"Formats:** {st.session_state.video_info['formats']}")

        format_options = ['mp4', 'mp3', 'avi']  # Add more formats if required
        selected_format = st.selectbox("Select Output Format:", format_options)

        if st.form_submit_button('Show Video'):
            file = utility.download_and_clip_youtube_video(youtube_link, start_time, end_time)
            if file is None:
                st.error("An error occurred while downloading the video")
            else:
                st.session_state['step_3'] = True
                st.session_state['video_file'] = file
                st.session_state['format_option'] = selected_format
                st.rerun()

if st.session_state['step_3'] and st.session_state['video_file']:
    st.info("The video displayed below is the best possible configuration available of the link you "
            "provided and not according to the format you provided.")
    st.video(st.session_state['video_file']['video'])
    if selected_format == 'mp3':
        st.success("Your file is ready to be downloaded")
        st.download_button(
            label="Download Processed File",
            data=st.session_state['video_file']['audio'].getvalue(),
            file_name=f"processed_file.{selected_format}",
            mime="audio/mp3"
        )
    else:
        with st.form('third_step'):
            st.markdown("#### Select resolution:")
            best_resolution = st.session_state.video_info['resolution']  # Assuming format like '720p'
            filtered_resolutions = [res for res in st.session_state.video_info['all_resolutions']]
            # filtered_resolutions.sort(reverse=True)  # Sort resolutions in descending order

            # Dropdown for resolution selection
            selected_resolution = st.selectbox(
                "Select Resolution:",
                [f"{res}p" for res in filtered_resolutions]
            )

            if st.form_submit_button("Process File"):
                with st.spinner("Processing the file..."):
                    width, height = map(int, selected_resolution[:-1].split('x'))
                    resolution_tuple = (width, height)
                    processed_file = utility.process_video_file(
                        input_file=st.session_state.video_file['video'],
                        output_format=st.session_state['format_option'],
                        resolution=resolution_tuple
                    )
                    if processed_file:
                        st.session_state['processed_file'] = processed_file
                        st.success("File processed successfully!")
                        st.session_state['step_4'] = True
                    else:
                        st.error("An error occurred during file processing.")

if st.session_state.step_4 and st.session_state['processed_file']:
    st.download_button(
        label="Download Processed File",
        data=st.session_state['processed_file'].getvalue(),
        file_name=f"{st.session_state.video_info['title']}.{selected_format}",
        mime="video/mp4" if selected_format == "mp4" else "audio/mp3"
    )

    st.success("File downloaded successfully!")

st.markdown("---")  # Add a horizontal line as a separator

st.markdown(
    """
    **Connect with me:**  
    [![GitHub](https://img.shields.io/badge/GitHub-100000?style=flat&logo=github&logoColor=white)](https://github.com/stunlec)  
    [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/shashwat-agarwal-5a36a3200/)
    """,
    unsafe_allow_html=True
)


