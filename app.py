import os
import base64
import binascii
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

def compress_image_before_encoding(image_path, output_image_path):
    """
    Compress the image before encoding to ensure it is below 900 KB.
    """
    img = Image.open(image_path)
    img.save(output_image_path, optimize=True, format="PNG")

    # Compress the image if needed before encoding
    while os.path.getsize(output_image_path) > 900 * 1024:  # File size over 900 KB
        img = Image.open(output_image_path)
        img = img.resize((img.width // 2, img.height // 2))  # Reduce size by half
        img.save(output_image_path, optimize=True, format="PNG")  # Save the compressed image again

def encode_text_into_plane(image, text, output_path, plane="RGB"):
    """
    Embed the text into a specific color plane (R, G, B, A).
    """
    img = image.convert("RGBA")  # Ensure image has alpha channel
    width, height = img.size
    binary_text = ''.join(format(ord(char), '08b') for char in text) + '00000000'  # Add terminator
    pixel_capacity = width * height  # Capacity per plane

    if len(binary_text) > pixel_capacity:
        raise ValueError("The message is too long for this image.")

    index = 0
    for y in range(height):
        for x in range(width):
            if index < len(binary_text):
                r, g, b, a = img.getpixel((x, y))

                # Embed into selected plane(s)
                if 'R' in plane:
                    r = (r & 0xFE) | int(binary_text[index])  # LSB of red
                if 'G' in plane:
                    g = (g & 0xFE) | int(binary_text[(index + 1) % len(binary_text)])  # LSB of green
                if 'B' in plane:
                    b = (b & 0xFE) | int(binary_text[(index + 2) % len(binary_text)])  # LSB of blue
                if 'A' in plane:
                    a = (a & 0xFE) | int(binary_text[(index + 3) % len(binary_text)])  # LSB of alpha

                img.putpixel((x, y), (r, g, b, a))
                index += 1 if 'A' in plane else 3  # Increment accordingly

    img.save(output_path, format="PNG")

def encode_zlib_into_image(image, file_data, output_path, plane="RGB"):
    """
    Embed zlib-compressed binary data into a specific color plane (R, G, B, A).
    """
    compressed_data = zlib.compress(file_data)
    binary_data = ''.join(format(byte, '08b') for byte in compressed_data) + '00000000'  # Add terminator
    width, height = image.size
    pixel_capacity = width * height  # Capacity per plane

    if len(binary_data) > pixel_capacity:
        raise ValueError("The compressed data is too long for this image.")

    img = image.convert("RGBA")  # Ensure image has alpha channel
    index = 0
    for y in range(height):
        for x in range(width):
            if index < len(binary_data):
                r, g, b, a = img.getpixel((x, y))

                # Embed into selected plane(s)
                if 'R' in plane:
                    r = (r & 0xFE) | int(binary_data[index])  # LSB of red
                if 'G' in plane:
                    g = (g & 0xFE) | int(binary_data[(index + 1) % len(binary_data)])  # LSB of green
                if 'B' in plane:
                    b = (b & 0xFE) | int(binary_data[(index + 2) % len(binary_data)])  # LSB of blue
                if 'A' in plane:
                    a = (a & 0xFE) | int(binary_data[(index + 3) % len(binary_data)])  # LSB of alpha

                img.putpixel((x, y), (r, g, b, a))
                index += 1 if 'A' in plane else 3  # Increment accordingly

    img.save(output_path, format="PNG")

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
    st.title("STEGOSAURUS WRECKS")

    st.info("You can use the default stock image or upload your own image.")
    uploaded_file = st.file_uploader("Choose an image...", type=["png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        image_path = uploaded_file
    else:
        default_image_path = "stegg.png"  # Path to your default stock image
        image_path = default_image_path
        st.image(image_path, caption="For the image to work properly you must click Encode Text first, then download from the generated link", use_column_width=True)
    
    # Allow the user to choose between embedding text or a zlib-compressed file
    option = st.radio("What do you want to embed?", ("Text", "Zlib Compressed File"))
    
    if option == "Text":
        master_plan = st.text_area("Enter text to encode into the image:", "")
        encoding_plane = st.selectbox("Select the plane to embed the text:", ["RGB", "R", "G", "B", "A"])
    else:
        uploaded_file_zlib = st.file_uploader("Upload a file to embed (it will be zlib compressed):", type=None)
        encoding_plane = st.selectbox("Select the plane to embed the compressed file:", ["RGB", "R", "G", "B", "A"])

    if st.button("Encode and Download"):
        st.info("Proceeding to encode data into the image.")

        # Set the output file path with the specific name
        output_image_path = "mystical_image_with_planes_and_zlib.png"

        # Compress the image before encoding to ensure it's under 900 KB
        compress_image_before_encoding(image_path, output_image_path)

        # If embedding text
        if option == "Text" and master_plan:
            image = Image.open(output_image_path)
            encode_text_into_plane(image, master_plan, output_image_path, encoding_plane)
            st.success(f"Text encoded into {encoding_plane} plane successfully.")
        
        # If embedding zlib file
        elif option == "Zlib Compressed File" and uploaded_file_zlib:
            file_data = uploaded_file_zlib.read()
            image = Image.open(output_image_path)
            encode_zlib_into_image(image, file_data, output_image_path, encoding_plane)
            st.success(f"Zlib compressed file encoded into {encoding_plane} plane successfully.")
        
        st.image(output_image_path, caption="MUST CLICK HYPERLINK TO DOWNLOAD PROPERLY", use_column_width=True)
        st.markdown(get_image_download_link(output_image_path), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
