import os
import cv2
import numpy as np
from tqdm import tqdm

# ===============================
# CONFIGURATION - PATH SETUP
# ===============================

BASE_PATH = r"C:\Users\Manar\Desktop\sPro\Lithology dataset\Lithology dataset"

PROCESSED_PATH = r"C:\Users\Manar\Desktop\sPro\processed"

IMG_SIZE = 224

CLASSES = ['limestone', 'sandstone', 'shale']
# CLASSES = ['limestone', 'sandstone', 'igneous']


# ===============================
# STEP 1: CREATE OUTPUT FOLDERS
# ===============================
print("=" * 60)
print("STEP 1: Creating output folders")
print("=" * 60)

# Create main processed folder
os.makedirs(PROCESSED_PATH, exist_ok=True)

# Create folders for each split and class
for split in ['train', 'val', 'test']:
    for class_name in CLASSES:
        folder_path = os.path.join(PROCESSED_PATH, split, class_name)
        os.makedirs(folder_path, exist_ok=True)
        print(f"✅ Created: {folder_path}")

# ===============================
# STEP 2: PROCESSING FUNCTION
# ===============================
def process_images(split_name):
    """
    Process all images for train/val/test split
    """
    print(f"\n{'=' * 60}")
    print(f"STEP 2: Processing {split_name.upper()} set")
    print(f"{'=' * 60}")
    
    total_processed = 0
    
    # Process each class
    for class_name in CLASSES:
        # Input path
        input_path = os.path.join(BASE_PATH, split_name, class_name)
        
        # Output path
        output_path = os.path.join(PROCESSED_PATH, split_name, class_name)
        
        # Check if input folder exists
        if not os.path.exists(input_path):
            print(f"⚠️  Warning: Folder not found: {input_path}")
            continue
        
        # Get list of image files
        image_files = [f for f in os.listdir(input_path) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.bmp'))]
        
        print(f"\n📁 Processing {class_name}: {len(image_files)} images")
        
        # Process each image with progress bar
        for image_file in tqdm(image_files, desc=f"    Progress", unit="img"):
            try:
                # 1. Read image
                image_path = os.path.join(input_path, image_file)
                image_bgr = cv2.imread(image_path)
                
                if image_bgr is None:
                    print(f"\n    ⚠️  Could not read: {image_file} - skipping")
                    continue
                
                # 2. Convert BGR to RGB
                image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
                
                # 3. Resize to 224x224
                image_resized = cv2.resize(image_rgb, (IMG_SIZE, IMG_SIZE))
                
                # 4. Normalize to 0-1 range
                image_normalized = image_resized.astype(np.float32) / 255.0
                
                # 5. Convert back to 0-255 for saving
                image_uint8 = (image_normalized * 255).astype(np.uint8)
                
                # 6. Convert back to BGR for saving
                image_bgr_final = cv2.cvtColor(image_uint8, cv2.COLOR_RGB2BGR)
                
                # 7. Save processed image
                output_file = os.path.join(output_path, image_file)
                cv2.imwrite(output_file, image_bgr_final)
                
                total_processed += 1
                
            except Exception as e:
                print(f"\n    ❌ Error processing {image_file}: {e}")
                continue
    
    return total_processed

# ===============================
# STEP 3: VERIFY DATASET EXISTS
# ===============================
print("\n" + "=" * 60)
print("CHECKING DATASET")
print("=" * 60)

# Check if dataset exists
if not os.path.exists(BASE_PATH):
    print(f"❌ ERROR: Dataset not found at:")
    print(f"   {BASE_PATH}")
    print("\nPlease make sure:")
    print("1. The 'Lithology dataset' folder is inside your sPro folder")
    print("2. The folder structure is: sPro/Lithology dataset/Lithology dataset/")
    print("3. Inside you have 'train', 'val', 'test' folders")
    exit()

print(f"✅ Dataset found at: {BASE_PATH}")

# Quick check of folder structure
all_good = True
for split in ['train', 'val', 'test']:
    split_path = os.path.join(BASE_PATH, split)
    if os.path.exists(split_path):
        print(f"✅ {split} folder exists")
        
        # Check class folders inside
        for class_name in CLASSES:
            class_path = os.path.join(split_path, class_name)
            if os.path.exists(class_path):
                print(f"   ✅ {class_name} folder exists")
            else:
                print(f"   ❌ {class_name} folder missing!")
                all_good = False
    else:
        print(f"❌ {split} folder missing!")
        all_good = False

if not all_good:
    print("\n⚠️  Some folders are missing! Please check your dataset structure.")
    response = input("Do you want to continue anyway? (yes/no): ")
    if response.lower() != 'yes':
        exit()

# ===============================
# STEP 4: RUN PROCESSING
# ===============================
print("\n" + "=" * 60)
print("🚀 STARTING PREPROCESSING PIPELINE")
print("=" * 60)

total_images = 0

# Process train, val, test in order
for split in ['train', 'val', 'test']:
    count = process_images(split)
    total_images += count
    print(f"\n✅ Finished {split}: {count} images processed")

# ===============================
# STEP 5: FINAL SUMMARY
# ===============================
print("\n" + "=" * 60)
print("🎉 PREPROCESSING COMPLETE!")
print("=" * 60)
print(f"📊 Total images processed: {total_images}")
print(f"📁 Processed images saved in: {PROCESSED_PATH}")
print("\nFolder structure created:")
print(f"   processed/")
print(f"   ├── train/")
print(f"   │   ├── limestone/  ({IMG_SIZE}x{IMG_SIZE} images)")
print(f"   │   ├── sandstone/  ({IMG_SIZE}x{IMG_SIZE} images)")
print(f"   │   └── shale/      ({IMG_SIZE}x{IMG_SIZE} images)")
print(f"   ├── val/")
print(f"   │   ├── limestone/")
print(f"   │   ├── sandstone/")
print(f"   │   └── shale/")
print(f"   └── test/")
print(f"       ├── limestone/")
print(f"       ├── sandstone/")
print(f"       └── shale/")
print("=" * 60)