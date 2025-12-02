# 🔧 Electrical Components Training Suite

**Complete training environment for electrical components detection in SLD diagrams**

This folder contains everything needed to train, evaluate, and deploy custom YOLO models for detecting electrical components.

## 🎯 What This Does

Creates a custom YOLO model that can detect:
- **CIRCUIT BREAKER** (Class 0) - Electrical switching devices
- **HRC FUSE** (Class 1) - High Rupturing Capacity fuses
- **ISOLATOR** (Class 2) - Circuit isolation switches

## 🚀 **SUPER QUICK START**

**Option 1: Complete Automated Setup**
```bash
# Windows
start_training.bat

# Linux/Mac
python setup_training.py
```

**Option 2: Manual Steps**
```bash
# 1. Prepare your data
python scripts/data_preparation.py

# 2. Train the model
python scripts/train_model.py --strategy single --model yolov8x

# 3. Evaluate performance
python scripts/evaluate_model.py --model models/production/electrical_components_best.pt
```

## 📁 Complete Folder Structure

```
electrical_training/
├── 📄 README.md                     # This comprehensive guide
├── 🚀 setup_training.py             # Complete automated setup
├── 🚀 start_training.bat            # Windows batch file
├── 📖 QUICK_START.md                # Quick reference guide
│
├── 📊 data/                         # Training datasets
│   ├── raw/                         # Original images and annotations
│   ├── processed/                   # Preprocessed training data
│   │   └── electrical_components/   # Final dataset structure
│   │       ├── images/              # Training images
│   │       │   ├── train/           # Training set
│   │       │   ├── val/             # Validation set
│   │       │   └── test/            # Test set
│   │       ├── labels/              # YOLO format labels
│   │       │   ├── train/           # Training labels
│   │       │   ├── val/             # Validation labels
│   │       │   └── test/            # Test labels
│   │       └── data.yaml            # Dataset configuration
│   ├── augmented/                   # Augmented training data
│   └── splits/                      # Train/val/test splits
│
├── 🤖 models/                       # Model files
│   ├── pretrained/                  # Base YOLO models (yolov8n.pt, yolov8x.pt, etc.)
│   ├── checkpoints/                 # Training checkpoints
│   ├── best/                        # Best trained models
│   └── production/                  # Production-ready models
│       └── electrical_components_best.pt  # Final trained model
│
├── ⚙️ configs/                      # Training configurations
│   ├── data_configs/                # Dataset configurations
│   │   └── electrical_components.yaml
│   └── training_configs/            # Training hyperparameters
│       ├── electrical_v1.yaml       # Standard training
│       ├── electrical_fast.yaml     # Fast training (testing)
│       └── electrical_production.yaml # Production training (best accuracy)
│
├── 🔧 scripts/                      # Training and utility scripts
│   ├── train_model.py               # Advanced training script
│   ├── evaluate_model.py            # Comprehensive evaluation
│   ├── data_preparation.py          # Data preprocessing
│   └── utils/                       # Utility functions
│
├── 📈 results/                      # Training results
│   ├── experiments/                 # Experiment logs and TensorBoard
│   ├── metrics/                     # Performance metrics (JSON)
│   └── visualizations/              # Training plots and charts
│
└── 📓 notebooks/                    # Jupyter notebooks for analysis
    ├── data_analysis.ipynb          # Dataset analysis
    ├── model_comparison.ipynb       # Model performance comparison
    └── training_analysis.ipynb      # Training process analysis
```

## 🎯 Training Strategies Available

### 1. **Single Model Training** (Recommended)
```bash
python scripts/train_model.py --strategy single --model yolov8x
```
- Best for production use
- Trains one high-quality model
- 2-4 hours training time

### 2. **Progressive Training** (Advanced)
```bash
python scripts/train_model.py --strategy progressive
```
- Stage 1: Fast training with YOLOv8s (30 min)
- Stage 2: Accurate training with YOLOv8x (3 hours)
- Best for experimentation

### 3. **Fast Training** (Testing)
```bash
python scripts/train_model.py --config configs/training_configs/electrical_fast.yaml
```
- Quick testing with YOLOv8s
- 30-60 minutes training time
- Lower accuracy but fast iteration

### 4. **Production Training** (Maximum Accuracy)
```bash
python scripts/train_model.py --config configs/training_configs/electrical_production.yaml
```
- Maximum accuracy settings
- 6-12 hours training time
- Best for final deployment

## 📊 **Training Algorithms & Best Practices Implemented**

### **Advanced YOLO Training Techniques:**
1. **Progressive Learning Rates** - Start high, gradually decrease
2. **Warmup Training** - Gradual learning rate increase at start
3. **Cosine Learning Rate Scheduling** - Smooth learning rate decay
4. **Mixed Precision Training** - Faster training with AMP
5. **Multi-Scale Training** - Train with different image sizes
6. **Advanced Data Augmentation** - Mosaic, MixUp, CopyPaste
7. **Label Smoothing** - Reduce overfitting
8. **Early Stopping** - Prevent overfitting

### **Electrical-Specific Optimizations:**
1. **High Resolution Training** (1024px) - Better small object detection
2. **Electrical Component Augmentation** - Line thickness, symbol size variation
3. **Class-Weighted Loss** - Handle imbalanced datasets
4. **Small Object Focus** - Optimized loss weights for electrical symbols
5. **Transfer Learning** - Start from COCO-pretrained weights

## 🎯 Performance Targets

| Metric | Target | Excellent | Good | Needs Improvement |
|--------|--------|-----------|------|-------------------|
| mAP@0.5 | >0.90 | >0.95 | 0.80-0.90 | <0.80 |
| mAP@0.5:0.95 | >0.75 | >0.85 | 0.65-0.75 | <0.65 |
| Precision | >0.85 | >0.90 | 0.75-0.85 | <0.75 |
| Recall | >0.85 | >0.90 | 0.75-0.85 | <0.75 |
| Inference Time | <50ms | <30ms | 30-50ms | >50ms |

## 🔧 Configuration Options

### **Latest YOLO11 Model Architectures:**
- **YOLO11n** - Fastest, nano model (2.6M params, 6.5B FLOPs)
- **YOLO11s** - Fast, small model (9.4M params, 21.5B FLOPs)
- **YOLO11m** - Balanced speed/accuracy (20.1M params, 68.0B FLOPs)
- **YOLO11l** - High accuracy (25.3M params, 86.9B FLOPs)
- **YOLO11x** - Maximum accuracy (56.9M params, 194.9B FLOPs) ⭐ **Recommended**

**YOLO11 Improvements over YOLOv8:**
- 22% fewer parameters with higher accuracy
- Enhanced feature extraction capabilities
- Optimized for efficiency and speed
- Better small object detection (perfect for electrical components)

### **YOLO11 Training Configurations:**
- **electrical_fast.yaml** - Quick testing with YOLO11n (50 epochs, 640px)
- **electrical_v1.yaml** - Standard YOLO11x training (300 epochs, 1280px) ⭐ **Recommended**
- **electrical_production.yaml** - Maximum accuracy YOLO11x (500 epochs, 1600px)
- **electrical_yolo11_latest.yaml** - Latest features with all YOLO11 optimizations ⭐ **NEW**

## 📈 Monitoring & Analysis

### **Real-time Monitoring:**
```bash
# TensorBoard (run during training)
tensorboard --logdir results/experiments

# Training logs
tail -f results/experiments/electrical_*/train.log
```

### **Post-Training Analysis:**
- **Metrics Dashboard** - `results/metrics/evaluation_*.json`
- **Training Plots** - `results/experiments/*/plots/`
- **Model Comparison** - `notebooks/model_comparison.ipynb`

## 🚀 **Integration with Web App**

After training, integrate with your SLD web application:

```bash
# Copy trained model to web app
copy models/production/electrical_components_best.pt ../web_app/core/backend/component_detection/models/electrical_components_yolo.pt

# Restart web app to use new model
cd ../web_app/core/backend
python main_fixed.py
```

## 🔍 **Troubleshooting**

### **Common Issues:**
1. **"Dataset not found"** - Run `python scripts/data_preparation.py` first
2. **"Out of memory"** - Reduce batch_size in config files
3. **"Low accuracy"** - Increase epochs, check data quality
4. **"Slow training"** - Use smaller model (yolov8s) or reduce image_size

### **Performance Optimization:**
1. **GPU Training** - Change `device: "cpu"` to `device: "0"` in configs
2. **Faster Training** - Use `electrical_fast.yaml` config
3. **Better Accuracy** - Use `electrical_production.yaml` config
4. **Memory Issues** - Reduce batch_size and image_size

## 📞 **Support & Next Steps**

1. **Start Training**: Run `python setup_training.py`
2. **Monitor Progress**: Check `results/experiments/`
3. **Evaluate Model**: Run evaluation script
4. **Deploy Model**: Copy to web app
5. **Iterate**: Adjust configs and retrain if needed

**🎉 You now have a complete, professional-grade training environment for electrical components detection!**
