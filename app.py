import os
import base64
import zlib
import streamlit as st
from PIL import Image

def convert_to_png(image_path):
    """
    Convert the image to PNG format if it's not already in PNG.
    Returns the path to the new PNG image.
    """
    img = Image.open(image_path)
    if img.format != 'PNG':
        new_image_path = os.path.splitext(image_path)[0] + '.png'
        img.save(new_image_path, 'PNG')  # Convert to PNG
        return new_image_path
    return image_path

def compress_image(image_path, output_image_path):
    """
    Compress the image without altering its dimensions to ensure it is below a certain size.
    """
    img = Image.open(image_path)
    img.save(output_image_path, optimize=True, format="PNG")

def embed_bits(value, bits, num_bits):
    """
    Embed `num_bits` bits into the least significant bits of `value`.
    """
    mask = (1 << num_bits) - 1
    value = (value & ~mask) | bits
    return value

def encode_text_into_plane(image, text, output_path, plane=["R", "G", "B"], bits_per_channel=2):
    """
    Embed the text into specified color planes using multiple bits per channel.
    """
    img = image.convert("RGBA")
    width, height = img.size
    binary_text = ''.join(format(ord(char), '08b') for char in text)
    total_bits_needed = len(binary_text)
    bits_per_pixel = bits_per_channel * len(plane)
    total_capacity = width * height * bits_per_pixel

    if total_bits_needed > total_capacity:
        raise ValueError(f"The message is too long for this image. Maximum capacity is {total_capacity // 8} characters.")

    idx = 0
    for y in range(height):
        for x in range(width):
            if idx >= total_bits_needed:
                break
            pixel = list(img.getpixel((x, y)))
            for i, color in enumerate(['R', 'G', 'B', 'A']):
                if color in plane and idx < total_bits_needed:
                    bits_to_embed = binary_text[idx:idx+bits_per_channel].ljust(bits_per_channel, '0')
                    bits = int(bits_to_embed, 2)
                    pixel[i] = embed_bits(pixel[i], bits, bits_per_channel)
                    idx += bits_per_channel
            img.putpixel((x, y), tuple(pixel))
        if idx >= total_bits_needed:
            break

    img.save(output_path, format="PNG")

def encode_zlib_into_image(image, file_data, output_path, plane=["R", "G", "B"], bits_per_channel=2):
    """
    Embed zlib-compressed binary data into specified color planes using multiple bits per channel.
    """
    compressed_data = zlib.compress(file_data)
    binary_data = ''.join(format(byte, '08b') for byte in compressed_data)
    total_bits_needed = len(binary_data)
    bits_per_pixel = bits_per_channel * len(plane)
    width, height = image.size
    total_capacity = width * height * bits_per_pixel

    if total_bits_needed > total_capacity:
        raise ValueError(f"The compressed data is too long for this image. Maximum capacity is {total_capacity // 8} bytes.")

    img = image.convert("RGBA")
    idx = 0
    for y in range(height):
        for x in range(width):
            if idx >= total_bits_needed:
                break
            pixel = list(img.getpixel((x, y)))
            for i, color in enumerate(['R', 'G', 'B', 'A']):
                if color in plane and idx < total_bits_needed:
                    bits_to_embed = binary_data[idx:idx+bits_per_channel].ljust(bits_per_channel, '0')
                    bits = int(bits_to_embed, 2)
                    pixel[i] = embed_bits(pixel[i], bits, bits_per_channel)
                    idx += bits_per_channel
            img.putpixel((x, y), tuple(pixel))
        if idx >= total_bits_needed:
            break

    img.save(output_path, format="PNG")

def calculate_max_message_length(image, plane, bits_per_channel):
    """
    Calculate the maximum number of characters that can be embedded.
    """
    width, height = image.size
    bits_per_pixel = bits_per_channel * len(plane)
    total_capacity = width * height * bits_per_pixel
    max_chars = total_capacity // 8  # 8 bits per character
    return max_chars

def get_image_download_link(img_path):
    """
    Generates a download link for the encoded image.
    """
    with open(img_path, "rb") as f:
        img_bytes = f.read()
    b64 = base64.b64encode(img_bytes).decode()
    href = f'<a href="data:image/png;base64,{b64}" download="{os.path.basename(img_path)}">Download {os.path.basename(img_path)}</a>'
    return href

def main():
    st.title("Steganography Encoder")

    st.info("You can embed text or zlib-compressed files into an image.")
    uploaded_file = st.file_uploader("Choose an image...", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        image_path = uploaded_file
        image = Image.open(image_path)
    else:
        default_image_path = "default_image.png"  # Provide a default image
        image_path = default_image_path
        image = Image.open(image_path)
        st.image(image_path, caption="Default Image", use_column_width=True)

    st.markdown("---")

    # Embedding options
    option = st.radio("Select what you want to embed:", ["Text", "Zlib Compressed File"], help="Choose between embedding text or a compressed binary file into the image.")

    # Select bits per channel
    bits_per_channel = st.slider("Bits per channel:", min_value=1, max_value=4, value=2,
                                 help="Select how many bits to use per color channel. More bits increase capacity but may degrade image quality.")

    # Select color planes
    encoding_plane = st.multiselect("Select the color planes for embedding:", ["R", "G", "B", "A"], default=["R", "G", "B"],
                                    help="Choose which color channels to use for embedding.")

    # Ensure at least one plane is selected
    if not encoding_plane:
        st.error("Please select at least one color plane for embedding.")
        return

    # Calculate maximum capacity
    max_chars = calculate_max_message_length(image, encoding_plane, bits_per_channel)
    st.write(f"Maximum message length: {max_chars} characters.")

    # Conditional UI based on the selection
    if option == "Text":
        st.subheader("Text Embedding Options")
        text_to_embed = st.text_area("Enter text to encode into the image:", "", help="Enter the text you want to hide in the image.")
    else:
        st.subheader("Zlib File Embedding Options")
        uploaded_file_zlib = st.file_uploader("Upload a file to embed (it will be zlib compressed):", type=None, help="Upload a file that will be compressed and hidden in the image.")

    st.markdown("---")

    # File path input with default value
    default_output_image_path = "encoded_image.png"
    output_image_path = st.text_input("Output File Path:", value=default_output_image_path, help="You can edit the output file path here.")

    if st.button("Encode and Download"):
        st.info("Processing...")

        # Compress the image without changing dimensions
        compress_image(image_path, output_image_path)

        # Open the compressed image for embedding
        image = Image.open(output_image_path)

        # If embedding text
        if option == "Text" and text_to_embed:
            try:
                encode_text_into_plane(image, text_to_embed, output_image_path, encoding_plane, bits_per_channel)
                st.success(f"Text successfully encoded into the {', '.join(encoding_plane)} plane(s).")
            except ValueError as e:
                st.error(str(e))
                return

        # If embedding zlib file
        elif option == "Zlib Compressed File" and uploaded_file_zlib:
            file_data = uploaded_file_zlib.read()
            try:
                encode_zlib_into_image(image, file_data, output_image_path, encoding_plane, bits_per_channel)
                st.success(f"Zlib compressed file successfully encoded into the {', '.join(encoding_plane)} plane(s).")
            except ValueError as e:
                st.error(str(e))
                return
        else:
            st.error("Please provide the content to embed.")
            return

        st.image(output_image_path, caption="Encoded Image", use_column_width=True)
        st.markdown(get_image_download_link(output_image_path), unsafe_allow_html=True)

        # Add balloons
        st.balloons()

if __name__ == "__main__":
    main()
