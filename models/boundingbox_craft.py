import easyocr
import cv2
import matplotlib.pyplot as plt

# Initialize CRAFT (EasyOCR)
reader = easyocr.Reader(['en'], gpu=False)

# Load an image
image_path = 'path_to_image.jpg'
image = cv2.imread(image_path)

# Perform text detection using CRAFT
bounds = reader.readtext(image_path)

# Display the detected text regions
for bound in bounds:
    # Each 'bound' contains a box and the detected text
    top_left, bottom_right = bound[0][0], bound[0][2]
    text = bound[1]
    score = bound[2]

    # Draw bounding box and display the text
    cv2.rectangle(image, tuple(top_left), tuple(bottom_right), (0, 255, 0), 2)
    cv2.putText(image, text, tuple(top_left), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

# Show the image with detected text regions
plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
plt.show()
