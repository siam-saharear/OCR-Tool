import os
import cv2

def scrape_image_paths(dir_path):
    files = os.listdir(dir_path)

    image_paths = []
    if len(files)==0:
        print("empty directory")
    else:
        for file in files:
            if file.split('.')[-1].lower() == "jpg" or file.split('.')[-1].lower() == "png":
                image_paths.append(os.path.join(dir_path, file)) 
            else:
                print("filetype not image")
    return image_paths


def rename_file(dir_path, file_path, new_name):
    if file_path:
        os.rename(file_path, os.path.join(dir_path, new_name))
        print(f"file {file_path.split('/')[-1]} renamed to --> {new_name}")


def resize_image(image, max_height=None, max_width=None, scale=None):
    height, width = image.shape[:2]
    if scale is None:
        aspect_ratio = width/height
        if max_height is not None:
            new_height = max_height
            if max_width is None:
                new_width = int(aspect_ratio*new_height)
            elif max_width is not None:
                print("aspect ratio cant be preserved. (max_height and max_width specified.)")
                new_width = max_width
        elif max_height is None:
            if max_width is not None:
                new_width = max_width
                new_height = int(new_width/aspect_ratio)
            else:
                new_height = height
                new_width = width
    elif scale is not None:
        new_height = int(height*scale)
        new_width = int(width*scale)

    resized_image = cv2.resize(image, (new_width, new_height))
    return resized_image




# dir_path = os.path.join("media", "input")
# images = scrape_image_paths(dir_path)
# for i in range(len(images)):
#     rename_file(dir_path, images[i], f"image_{i+1}.png")