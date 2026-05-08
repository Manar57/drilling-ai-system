import os
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
import matplotlib.pyplot as plt
import numpy as np

# ===============================
# CONFIGURATION
# ===============================

PROCESSED_PATH = r"C:\Users\Manar\Desktop\sPro\processed"
MODEL_SAVE_PATH = r"C:\Users\Manar\Desktop\sPro\models\rock_classifier.h5"

IMG_SIZE = 224
BATCH_SIZE = 32
EPOCHS_PHASE_1 = 15     
EPOCHS_PHASE_2 = 10      
LEARNING_RATE_PHASE_1 = 0.0001
LEARNING_RATE_PHASE_2 = 0.00001  

CLASSES = ['limestone', 'sandstone', 'shale']

# CLASSES = ['limestone', 'sandstone', 'igneous']
NUM_CLASSES = len(CLASSES)

# ===============================
# STEP 1: DATA AUGMENTATION & LOADING
# ===============================
print("=" * 60)
print("STEP 1: Preparing data generators")
print("=" * 60)

train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=15,         
    width_shift_range=0.1,      
    height_shift_range=0.1,
    zoom_range=0.1,            
    horizontal_flip=True,
    fill_mode='nearest'
)

valid_test_datagen = ImageDataGenerator(rescale=1./255)

train_generator = train_datagen.flow_from_directory(
    os.path.join(PROCESSED_PATH, 'train'),
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    classes=CLASSES,
    shuffle=True
)

val_generator = valid_test_datagen.flow_from_directory(
    os.path.join(PROCESSED_PATH, 'val'),
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    classes=CLASSES,
    shuffle=False
)

test_generator = valid_test_datagen.flow_from_directory(
    os.path.join(PROCESSED_PATH, 'test'),
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    classes=CLASSES,
    shuffle=False
)

print(f"\n✅ Classes mapping: {train_generator.class_indices}")
print(f"✅ Train samples: {train_generator.samples}")
print(f"✅ Validation samples: {val_generator.samples}")
print(f"✅ Test samples: {test_generator.samples}")

# ===============================
# STEP 2: BUILD THE MODEL (Transfer Learning)
# ===============================
print("\n" + "=" * 60)
print("STEP 2: Building model with MobileNetV2")
print("=" * 60)

# Load base model (MobileNetV2)
base_model = MobileNetV2(
    input_shape=(IMG_SIZE, IMG_SIZE, 3),
    include_top=False,
    weights='imagenet'
)

# Freeze base model layers
base_model.trainable = False

odel = models.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dense(256, activation='relu'),       
    layers.Dropout(0.4),                        
    layers.Dense(NUM_CLASSES, activation='softmax')
])

model.summary()

# ===============================
# STEP 3: COMPILE THE MODEL (Phase 1)
# ===============================
print("\n" + "=" * 60)
print("STEP 3: Phase 1 - Training top layers")
print("=" * 60)

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE_PHASE_1),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

print("✅ Model compiled for Phase 1")

# ===============================
# STEP 4: CALLBACKS
# ===============================
print("\n" + "=" * 60)
print("STEP 4: Setting up callbacks")
print("=" * 60)

os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)

callbacks = [
    ModelCheckpoint(
        MODEL_SAVE_PATH,
        monitor='val_accuracy',
        save_best_only=True,
        mode='max',
        verbose=1
    ),
    EarlyStopping(
        monitor='val_accuracy',
        patience=5,
        restore_best_weights=True,
        verbose=1
    ),
    ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=3,
        min_lr=1e-7,
        verbose=1
    )
]

print("✅ Callbacks ready")

# ===============================
# STEP 5: PHASE 1 - TRAINING TOP LAYERS
# ===============================
print("\n" + "=" * 60)
print(f"STEP 5: Phase 1 - Training ({EPOCHS_PHASE_1} epochs)")
print("=" * 60)
print(f"📊 Training on {train_generator.samples} images")
print(f"📊 Validating on {val_generator.samples} images")
print(f"⚙️ Learning rate: {LEARNING_RATE_PHASE_1}")
print("=" * 60)

history_phase1 = model.fit(
    train_generator,
    steps_per_epoch=train_generator.samples // BATCH_SIZE,
    epochs=EPOCHS_PHASE_1,
    validation_data=val_generator,
    validation_steps=val_generator.samples // BATCH_SIZE,
    callbacks=callbacks,
    verbose=1
)

print("\n✅ Phase 1 completed!")

# ===============================
# STEP 6: PHASE 2 - FINE-TUNING
# ===============================
print("\n" + "=" * 60)
print(f"STEP 6: Phase 2 - Fine-tuning ({EPOCHS_PHASE_2} epochs)")
print("=" * 60)

# Unfreeze last 50 layers for fine-tuning
base_model.trainable = True
for layer in base_model.layers[:-50]:
    layer.trainable = False

# Recompile with lower learning rate
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE_PHASE_2),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

print(f"⚙️ Learning rate reduced to: {LEARNING_RATE_PHASE_2}")
print("🔓 Unfroze last 50 layers for fine-tuning")

# Continue training
history_phase2 = model.fit(
    train_generator,
    steps_per_epoch=train_generator.samples // BATCH_SIZE,
    epochs=EPOCHS_PHASE_2,
    validation_data=val_generator,
    validation_steps=val_generator.samples // BATCH_SIZE,
    callbacks=callbacks,
    verbose=1
)

print("\n✅ Phase 2 (Fine-tuning) completed!")

# ===============================
# STEP 7: EVALUATE ON TEST SET
# ===============================
print("\n" + "=" * 60)
print("STEP 7: Evaluating on test set")
print("=" * 60)

# Load best model
best_model = tf.keras.models.load_model(MODEL_SAVE_PATH)

test_loss, test_accuracy = best_model.evaluate(test_generator, verbose=1)
print(f"\n🎯 Test Accuracy: {test_accuracy:.4f} ({test_accuracy*100:.2f}%)")
print(f"📉 Test Loss: {test_loss:.4f}")

# ===============================
# STEP 8: PLOT TRAINING HISTORY
# ===============================
print("\n" + "=" * 60)
print("STEP 8: Plotting training history")
print("=" * 60)

# Combine both phases for plotting
total_epochs = len(history_phase1.history['accuracy']) + len(history_phase2.history['accuracy'])

plt.figure(figsize=(14, 5))

# Plot accuracy
plt.subplot(1, 2, 1)
plt.plot(history_phase1.history['accuracy'], label='Train Acc (Phase 1)')
plt.plot(history_phase1.history['val_accuracy'], label='Val Acc (Phase 1)')
plt.plot(range(len(history_phase1.history['accuracy']), total_epochs), 
         history_phase2.history['accuracy'], label='Train Acc (Phase 2)')
plt.plot(range(len(history_phase1.history['val_accuracy']), total_epochs), 
         history_phase2.history['val_accuracy'], label='Val Acc (Phase 2)')
plt.title('Model Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()
plt.grid(True)

# Plot loss
plt.subplot(1, 2, 2)
plt.plot(history_phase1.history['loss'], label='Train Loss (Phase 1)')
plt.plot(history_phase1.history['val_loss'], label='Val Loss (Phase 1)')
plt.plot(range(len(history_phase1.history['loss']), total_epochs), 
         history_phase2.history['loss'], label='Train Loss (Phase 2)')
plt.plot(range(len(history_phase1.history['val_loss']), total_epochs), 
         history_phase2.history['val_loss'], label='Val Loss (Phase 2)')
plt.title('Model Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.grid(True)

# Save plot
plot_path = os.path.join(os.path.dirname(MODEL_SAVE_PATH), 'training_history.png')
plt.savefig(plot_path, dpi=150)
print(f"✅ Training plot saved to: {plot_path}")

plt.show()

# ===============================
# STEP 9: SAMPLE PREDICTIONS
# ===============================
print("\n" + "=" * 60)
print("STEP 9: Sample predictions from test set")
print("=" * 60)

# Take a batch from test set
sample_images, sample_labels = next(test_generator)

# Predict
predictions = best_model.predict(sample_images)
predicted_classes = np.argmax(predictions, axis=1)
true_classes = np.argmax(sample_labels, axis=1)

# Print results
print("\n📸 Sample predictions (first 15 images):")
print("-" * 60)
print(f"{'#':<4} {'True Class':<15} {'Predicted':<15} {'Confidence':<12} {'Status':<8}")
print("-" * 60)

correct_count = 0
for i in range(min(15, len(sample_images))):
    true_label = CLASSES[true_classes[i]]
    pred_label = CLASSES[predicted_classes[i]]
    confidence = predictions[i][predicted_classes[i]]
    is_correct = true_classes[i] == predicted_classes[i]
    if is_correct:
        correct_count += 1
        status = "✅"
    else:
        status = "❌"
    print(f"{i+1:<4} {true_label:<15} {pred_label:<15} {confidence:.4f}       {status}")

print("-" * 60)
print(f"📊 Sample accuracy (first 15): {correct_count}/15 = {correct_count/15*100:.1f}%")

# ===============================
# STEP 10: FINAL SUMMARY
# ===============================
print("\n" + "=" * 60)
print("🎉 MODEL TRAINING COMPLETE!")
print("=" * 60)
print(f"📁 Model saved to: {MODEL_SAVE_PATH}")
print(f"📊 Final Test Accuracy: {test_accuracy*100:.2f}%")
print(f"📉 Final Test Loss: {test_loss:.4f}")
print("=" * 60)

# Check target accuracy
if test_accuracy >= 0.90:
    print("🎉 EXCELLENT! Target achieved: Accuracy ≥ 90%")
elif test_accuracy >= 0.85:
    print("✅ Good! Accuracy ≥ 85%")
elif test_accuracy >= 0.80:
    print("✅ Target achieved: Accuracy ≥ 80%")
else:
    print(f"⚠️ Target not yet achieved: {test_accuracy*100:.2f}% < 80%")
    print("   Suggestions:")
    print("   - Increase epochs")
    print("   - Adjust learning rate")
    print("   - Add more data augmentation")
print("=" * 60)