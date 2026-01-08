import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import cv2
import numpy as np
import json
import time
import math
from datetime import datetime
import pyautogui
from collections import deque

latest_calibration_file = None

mirror_preview = True
class PureEyeCalibrator:
    
    def __init__(self):
        self.screen_w, self.screen_h = pyautogui.size()
        
        self.calibration_points = self.generate_calibration_grid()
        self.current_point_index = 0
        
        self.eye_data = []
        self.screen_data = []
        self.collection_frames = 0
        self.frames_per_point = 45
        
        self.baseline_head_position = None
        self.head_movement_threshold = 12
        
        self.is_collecting = False
        self.calibration_complete = False
        self.transformation_matrix = None
        
        self.landmark_screen_mapping = {}
        self.screen_region_landmarks = {}
        self.landmark_patterns = []
        
        self.screen_boundary_margin = 0.15
        self.off_screen_gaze_data = []
        
        print("🎯 Pure Eye Movement Calibrator initialized")
        print(f"📺 Screen: {self.screen_w}x{self.screen_h}")
        print("📋 Calibration will use 25-point grid for better accuracy")
        print("🔍 Will detect screen boundary for gaze control")
    
    def generate_calibration_grid(self):
        points = []
        
        margin_x = int(self.screen_w * 0.08)
        margin_y = int(self.screen_h * 0.08)
        
        grid_w = self.screen_w - 2 * margin_x
        grid_h = self.screen_h - 2 * margin_y
        
        for row in range(5):
            for col in range(5):
                x = margin_x + col * (grid_w // 4)
                y = margin_y + row * (grid_h // 4)
                points.append((x, y))
        
        corner_margin = 20
        extra_points = [
            (corner_margin, corner_margin),
            (self.screen_w - corner_margin, corner_margin),
            (corner_margin, self.screen_h - corner_margin),
            (self.screen_w - corner_margin, self.screen_h - corner_margin),
        ]
        
        points.extend(extra_points)
        
        print(f"📍 Generated {len(points)} calibration points")
        return points
    
    def get_head_position(self, landmarks, w, h):
        """Get head center position for movement detection using MediaPipe Face Mesh"""
        key_points = [1, 175, 234, 454, 10, 152] 
        
        positions = []
        for idx in key_points:
            if idx < len(landmarks.landmark):
                point = landmarks.landmark[idx]
                positions.append([point.x * w, point.y * h])
        
        if len(positions) > 0:
            return np.mean(positions, axis=0)
        else:
            return np.array([w/2, h/2]) 
    
    def get_eye_position(self, landmarks, w, h):
        """Get ultra-precise eye position using COMPLETE MediaPipe Face Mesh analysis"""
        try:
            landmark_signature = self.extract_landmark_signature(landmarks, w, h)
            
            left_eye_full = {
                'iris': [474, 475, 476, 477],             
                'corners': [33, 133],                      
                'upper_lid': [159, 158, 157, 173, 133],   
                'lower_lid': [144, 145, 153, 154, 155],    
                'center_region': [468, 469, 470, 471]      
            }
            
            right_eye_full = {
                'iris': [469, 470, 471, 472],            
                'corners': [362, 263],                      
                'upper_lid': [386, 385, 384, 398, 263],  
                'lower_lid': [373, 374, 380, 381, 382],  
                'center_region': [473, 474, 475, 476]      
            }
            
            left_analysis = self._analyze_eye_region(landmarks, left_eye_full, w, h, 'left')
            right_analysis = self._analyze_eye_region(landmarks, right_eye_full, w, h, 'right')
            
            combined_signature = {
                'landmark_signature': landmark_signature,
                'left_analysis': left_analysis,
                'right_analysis': right_analysis,
                'timestamp': time.time()
            }
            
            if left_analysis['quality'] > 0.7 and right_analysis['quality'] > 0.7:
                combined_gaze = self._combine_eye_measurements(left_analysis, right_analysis)
                combined_signature['final_position'] = combined_gaze['position']
                return combined_gaze['position']
            elif left_analysis['quality'] > right_analysis['quality']:
                combined_signature['final_position'] = left_analysis['gaze_vector']
                return left_analysis['gaze_vector']
            else:
                combined_signature['final_position'] = right_analysis['gaze_vector']
                return right_analysis['gaze_vector']
                
        except Exception as e:
            print(f"Warning: Complete eye analysis failed: {e}")
            return self.get_fallback_eye_position(landmarks, w, h)
    
    def extract_landmark_signature(self, landmarks, w, h):
        """Extract comprehensive landmark signature for gaze pattern recognition"""
        signature = {}
        
        try:
            key_landmarks = {
                'left_iris': [474, 475, 476, 477],
                'left_corners': [33, 133],
                'left_upper': [159, 158, 157],
                'left_lower': [144, 145, 153],
                
                'right_iris': [469, 470, 471, 472],
                'right_corners': [362, 263],
                'right_upper': [386, 385, 384],
                'right_lower': [373, 374, 380],
                
                'nose_tip': [1],
                'face_center': [10],
                'chin': [175],
            }
            
            for group_name, indices in key_landmarks.items():
                group_points = []
                for idx in indices:
                    if idx < len(landmarks.landmark):
                        point = landmarks.landmark[idx]
                        norm_x = point.x * w
                        norm_y = point.y * h
                        group_points.append([norm_x, norm_y])
                
                if len(group_points) > 0:
                    centroid = np.mean(group_points, axis=0)
                    relative_positions = np.array(group_points) - centroid
                    
                    signature[group_name] = {
                        'centroid': centroid.tolist(),
                        'relative_positions': relative_positions.tolist(),
                        'variance': np.var(group_points, axis=0).tolist()
                    }
            
            if 'left_iris' in signature and 'right_iris' in signature:
                left_center = np.array(signature['left_iris']['centroid'])
                right_center = np.array(signature['right_iris']['centroid'])
                
                signature['eye_relationship'] = {
                    'distance': np.linalg.norm(right_center - left_center),
                    'angle': np.arctan2(right_center[1] - left_center[1], 
                                      right_center[0] - left_center[0]),
                    'midpoint': ((left_center + right_center) / 2).tolist()
                }
            
            return signature
            
        except Exception as e:
            print(f"Landmark signature extraction failed: {e}")
            return {}
    
    def _analyze_eye_region(self, landmarks, eye_landmarks, w, h, eye_side):
        """Comprehensive analysis of single eye region using all available landmarks"""
        analysis = {
            'quality': 0.0,
            'gaze_vector': np.array([w/2, h/2]),
            'iris_center': None,
            'eye_corners': None,
            'lid_positions': None,
            'micro_movements': None
        }
        
        try:
            iris_points = []
            for idx in eye_landmarks['iris']:
                if idx < len(landmarks.landmark):
                    point = landmarks.landmark[idx]
                    iris_points.append([point.x * w, point.y * h, point.z if hasattr(point, 'z') else 0])
            
            if len(iris_points) >= 4:
                iris_points = np.array(iris_points)
                
                if iris_points.shape[1] > 2:
                    z_weights = 1.0 / (np.abs(iris_points[:, 2]) + 0.1)
                else:
                    z_weights = np.ones(len(iris_points))
                
                iris_center_2d = np.average(iris_points[:, :2], axis=0, weights=z_weights)
                analysis['iris_center'] = iris_center_2d
                
                eye_center = self._get_eye_geometric_center(landmarks, eye_landmarks, w, h)
                iris_displacement = iris_center_2d - eye_center
                
                sensitivity_multiplier = 3.5 
                amplified_displacement = iris_displacement * sensitivity_multiplier
                
                analysis['gaze_vector'] = eye_center + amplified_displacement
                analysis['micro_movements'] = iris_displacement
                analysis['quality'] = 0.9
            
            corner_points = []
            for idx in eye_landmarks['corners']:
                if idx < len(landmarks.landmark):
                    point = landmarks.landmark[idx]
                    corner_points.append([point.x * w, point.y * h])
            
            if len(corner_points) >= 2:
                analysis['eye_corners'] = np.array(corner_points)
                
            upper_lid = []
            lower_lid = []
            
            for idx in eye_landmarks['upper_lid']:
                if idx < len(landmarks.landmark):
                    point = landmarks.landmark[idx]
                    upper_lid.append([point.x * w, point.y * h])
                    
            for idx in eye_landmarks['lower_lid']:
                if idx < len(landmarks.landmark):
                    point = landmarks.landmark[idx]
                    lower_lid.append([point.x * w, point.y * h])
            
            if len(upper_lid) >= 3 and len(lower_lid) >= 3:
                analysis['lid_positions'] = {
                    'upper': np.array(upper_lid),
                    'lower': np.array(lower_lid)
                }
                
                eye_height = np.mean(upper_lid, axis=0)[1] - np.mean(lower_lid, axis=0)[1]
                if eye_height > 8:  # Eye reasonably open
                    analysis['quality'] = min(analysis['quality'] + 0.1, 1.0)
            
            return analysis
            
        except Exception as e:
            print(f"Eye region analysis failed for {eye_side}: {e}")
            analysis['quality'] = 0.1
            return analysis
    
    def _get_eye_geometric_center(self, landmarks, eye_landmarks, w, h):
        """Calculate geometric center of eye region"""
        all_points = []
        
        for landmark_set in eye_landmarks.values():
            for idx in landmark_set:
                if idx < len(landmarks.landmark):
                    point = landmarks.landmark[idx]
                    all_points.append([point.x * w, point.y * h])
        
        if len(all_points) > 0:
            return np.mean(all_points, axis=0)
        else:
            return np.array([w/2, h/2])
    
    def _combine_eye_measurements(self, left_analysis, right_analysis):
        """Combine left and right eye measurements for maximum accuracy"""
        left_weight = left_analysis['quality']
        right_weight = right_analysis['quality']
        total_weight = left_weight + right_weight
        
        if total_weight > 0:
            left_weight /= total_weight
            right_weight /= total_weight
            
            combined_position = (left_analysis['gaze_vector'] * left_weight + 
                               right_analysis['gaze_vector'] * right_weight)
            
            if (left_analysis['micro_movements'] is not None and 
                right_analysis['micro_movements'] is not None):
                combined_micro = (left_analysis['micro_movements'] * left_weight +
                                right_analysis['micro_movements'] * right_weight)
            else:
                combined_micro = None
                
            return {
                'position': combined_position,
                'micro_movements': combined_micro,
                'quality': (left_analysis['quality'] + right_analysis['quality']) / 2
            }
        else:
            return {
                'position': np.array([w/2, h/2]),
                'micro_movements': None,
                'quality': 0.0
            }
    
    def get_fallback_eye_position(self, landmarks, w, h):
        """Fallback eye position using eye corner landmarks"""
        left_eye_corners = [33, 133]  
        right_eye_corners = [362, 263] 
        
        try:
            eye_points = []
            for idx in left_eye_corners + right_eye_corners:
                if idx < len(landmarks.landmark):
                    point = landmarks.landmark[idx]
                    eye_points.append([point.x * w, point.y * h])
            
            if len(eye_points) >= 2:
                return np.mean(eye_points, axis=0)
            else:
                return np.array([w/2, h/2])
                
        except:
            return np.array([w/2, h/2])
    
    def check_head_movement(self, current_head_pos):
        """Check if head moved significantly"""
        if self.baseline_head_position is None:
            self.baseline_head_position = current_head_pos
            return False
        
        distance = np.linalg.norm(current_head_pos - self.baseline_head_position)
        return distance > self.head_movement_threshold
    
    def collect_calibration_point(self, eye_pos, screen_pos):
        """Collect data for current calibration point with landmark-based mapping"""
        if self.is_valid_eye_data(eye_pos):
            self.eye_data.append(eye_pos.copy())
            self.screen_data.append(screen_pos)
            
            if hasattr(self, '_current_landmark_signature'):
                landmark_pattern = {
                    'screen_position': screen_pos,
                    'landmark_signature': self._current_landmark_signature,
                    'eye_position': eye_pos.copy()
                }
                self.landmark_patterns.append(landmark_pattern)
                
                region_key = self._get_screen_region_key(screen_pos)
                if region_key not in self.screen_region_landmarks:
                    self.screen_region_landmarks[region_key] = []
                self.screen_region_landmarks[region_key].append(landmark_pattern)
            
            self.collection_frames += 1
        else:
            print(f"⚠️  Skipping invalid eye data: {eye_pos}")
            return
        
        if self.collection_frames >= self.frames_per_point:
            total_points = len(self.calibration_points)
            print(f"✅ Point {self.current_point_index + 1}/{total_points} completed")
            
            point_start = len(self.eye_data) - self.frames_per_point
            point_data = self.eye_data[point_start:]
            if self.validate_point_data(point_data):
                print(f"📊 Point data quality: Good")
                self._create_landmark_mapping(self.current_point_index)
            else:
                print(f"⚠️  Point data quality: Poor - consider recollecting")
            
            self.current_point_index += 1
            self.collection_frames = 0
            self.is_collecting = False
            self.baseline_head_position = None  
            
            if self.current_point_index >= len(self.calibration_points):
                self.complete_calibration()
    
    def _get_screen_region_key(self, screen_pos):
        """Convert screen position to region key for landmark mapping"""
        x, y = screen_pos
        grid_x = int(x / (self.screen_w / 5)) 
        grid_y = int(y / (self.screen_h / 5))
        
        grid_x = max(0, min(grid_x, 4))
        grid_y = max(0, min(grid_y, 4))
        
        return f"region_{grid_x}_{grid_y}"
    
    def _create_landmark_mapping(self, point_index):
        """Create landmark-to-screen mapping for calibration point"""
        if point_index < len(self.calibration_points):
            screen_pos = self.calibration_points[point_index]
            
            point_patterns = [p for p in self.landmark_patterns 
                            if np.allclose(p['screen_position'], screen_pos, atol=10)]
            
            if len(point_patterns) > 0:
                averaged_signature = self._average_landmark_signatures([p['landmark_signature'] for p in point_patterns])
                
                mapping_key = f"point_{point_index}"
                self.landmark_screen_mapping[mapping_key] = {
                    'screen_position': screen_pos,
                    'landmark_signature': averaged_signature,
                    'pattern_count': len(point_patterns),
                    'quality_score': self._calculate_pattern_quality(point_patterns)
                }
                
                print(f"📍 Created landmark mapping for point {point_index + 1}: {len(point_patterns)} patterns")
    
    def _average_landmark_signatures(self, signatures):
        """Average multiple landmark signatures for robust mapping"""
        if not signatures:
            return {}
        
        averaged = {}
        
        common_keys = set(signatures[0].keys())
        for sig in signatures[1:]:
            common_keys = common_keys.intersection(set(sig.keys()))
        
        for key in common_keys:
            if key in signatures[0]:
                if 'centroid' in signatures[0][key]:
                    centroids = [sig[key]['centroid'] for sig in signatures if key in sig]
                    averaged[key] = {
                        'centroid': np.mean(centroids, axis=0).tolist(),
                        'variance': np.var(centroids, axis=0).tolist()
                    }
        
        return averaged
    
    def _calculate_pattern_quality(self, patterns):
        """Calculate quality score for landmark patterns"""
        if len(patterns) < 3:
            return 0.5
        
        eye_positions = [p['eye_position'] for p in patterns]
        variance = np.var(eye_positions, axis=0)
        consistency = 1.0 / (1.0 + np.mean(variance))
        
        return min(max(consistency, 0.0), 1.0)
    
    def complete_calibration(self):
        """Complete calibration and compute transformation matrix"""
        print("🧮 Computing calibration transformation...")
        
        eye_points = np.array(self.eye_data, dtype=np.float32)
        screen_points = np.array(self.screen_data, dtype=np.float32)
        
        self.transformation_matrix = self.compute_transformation_matrix(eye_points, screen_points)
        
        filename = self.save_calibration()
        try:
            self.saved_filename = filename
            global latest_calibration_file
            latest_calibration_file = filename
        except Exception:
            pass

        self.calibration_complete = True
        print("🎉 Calibration completed successfully!")
        print(f"💾 Calibration saved to: {filename}")
        print("👀 You can now control cursor with pure eye movement!")
    
    def compute_transformation_matrix(self, eye_points, screen_points):
        """Compute transformation from eye coordinates to screen coordinates with improved robustness"""
        print(f"🔧 Computing transformation with {len(eye_points)} data points...")
        
        eye_points, screen_points = self.remove_outliers(eye_points, screen_points)
        print(f"📊 After outlier removal: {len(eye_points)} points remain")
        
        if len(eye_points) < 20:  
            print("⚠️  Warning: Few points remaining after outlier removal")
        
        n_points = len(eye_points)
        
        eye_mean = np.mean(eye_points, axis=0)
        eye_std = np.std(eye_points, axis=0) + 1e-8  
        eye_normalized = (eye_points - eye_mean) / eye_std
        
        A_linear = np.zeros((n_points, 3))
        A_linear[:, 0] = 1  # constant term
        A_linear[:, 1] = eye_normalized[:, 0] 
        A_linear[:, 2] = eye_normalized[:, 1] 
        
        alpha = 0.1 
        I = np.eye(3)
        
        x_coeffs_linear = np.linalg.solve(A_linear.T @ A_linear + alpha * I, A_linear.T @ screen_points[:, 0])
        y_coeffs_linear = np.linalg.solve(A_linear.T @ A_linear + alpha * I, A_linear.T @ screen_points[:, 1])
        
        linear_pred = A_linear @ np.column_stack([x_coeffs_linear, y_coeffs_linear])
        linear_error = np.mean(np.linalg.norm(linear_pred - screen_points, axis=1))
        
        print(f"📈 Linear transformation error: {linear_error:.1f} pixels")
        
        if n_points >= 50 and linear_error > 80:
            print("🔄 Trying polynomial transformation...")
            
            A = np.zeros((n_points, 6))
            A[:, 0] = 1 
            A[:, 1] = eye_normalized[:, 0]  
            A[:, 2] = eye_normalized[:, 1] 
            A[:, 3] = eye_normalized[:, 0] ** 2 
            A[:, 4] = eye_normalized[:, 1] ** 2  
            A[:, 5] = eye_normalized[:, 0] * eye_normalized[:, 1] 
            
            I_poly = np.eye(6)
            alpha_poly = 1.0 
            
            x_coeffs = np.linalg.solve(A.T @ A + alpha_poly * I_poly, A.T @ screen_points[:, 0])
            y_coeffs = np.linalg.solve(A.T @ A + alpha_poly * I_poly, A.T @ screen_points[:, 1])
            
            poly_pred = A @ np.column_stack([x_coeffs, y_coeffs])
            poly_error = np.mean(np.linalg.norm(poly_pred - screen_points, axis=1))
            
            print(f"📈 Polynomial transformation error: {poly_error:.1f} pixels")
            
            if poly_error < linear_error * 0.8:
                print("✅ Using polynomial transformation")
                transformation_type = "polynomial"
            else:
                print("✅ Using linear transformation (polynomial not better)")
                x_coeffs = np.pad(x_coeffs_linear, (0, 3), 'constant') 
                y_coeffs = np.pad(y_coeffs_linear, (0, 3), 'constant')
                transformation_type = "linear"
        else:
            print("✅ Using linear transformation")
            x_coeffs = np.pad(x_coeffs_linear, (0, 3), 'constant')
            y_coeffs = np.pad(y_coeffs_linear, (0, 3), 'constant')
            transformation_type = "linear"
        
        transformation = {
            'x_coeffs': x_coeffs.tolist(),
            'y_coeffs': y_coeffs.tolist(),
            'eye_data': eye_points.tolist(),
            'screen_data': screen_points.tolist(),
            'normalization': {
                'eye_mean': eye_mean.tolist(),
                'eye_std': eye_std.tolist()
            },
            'transformation_type': transformation_type
        }
        
        predicted_screen = self.apply_transformation(eye_points, transformation)
        errors = predicted_screen - screen_points
        rmse_x = np.sqrt(np.mean(errors[:, 0] ** 2))
        rmse_y = np.sqrt(np.mean(errors[:, 1] ** 2))
        
        print(f"📊 Final RMSE: X={rmse_x:.1f}px, Y={rmse_y:.1f}px")
        
        transformation['accuracy'] = {
            'rmse_x': rmse_x,
            'rmse_y': rmse_y,
            'total_rmse': np.sqrt(rmse_x**2 + rmse_y**2)
        }
        
        print(f"📊 Calibration accuracy: {transformation['accuracy']['total_rmse']:.1f} pixels RMSE")
        
        return transformation
    
    def apply_transformation(self, eye_points, transformation=None):
        """Apply transformation to convert eye coordinates to screen coordinates"""
        if transformation is None:
            transformation = self.transformation_matrix
        
        if transformation is None:
            return eye_points 
        
        x_coeffs = np.array(transformation['x_coeffs'])
        y_coeffs = np.array(transformation['y_coeffs'])
        
        if eye_points.ndim == 1:
            eye_points = eye_points.reshape(1, -1)
        
        n_points = eye_points.shape[0]
        
        if 'normalization' in transformation:
            eye_mean = np.array(transformation['normalization']['eye_mean'])
            eye_std = np.array(transformation['normalization']['eye_std'])
            eye_normalized = (eye_points - eye_mean) / eye_std
        else:
            eye_normalized = eye_points
        
        transformation_type = transformation.get('transformation_type', 'polynomial')
        
        if transformation_type == 'linear':
            A = np.zeros((n_points, 6))
            A[:, 0] = 1
            A[:, 1] = eye_normalized[:, 0]
            A[:, 2] = eye_normalized[:, 1]
        else:
            A = np.zeros((n_points, 6))
            A[:, 0] = 1
            A[:, 1] = eye_normalized[:, 0]
            A[:, 2] = eye_normalized[:, 1]
            A[:, 3] = eye_normalized[:, 0] ** 2
            A[:, 4] = eye_normalized[:, 1] ** 2
            A[:, 5] = eye_normalized[:, 0] * eye_normalized[:, 1]
        
        screen_x = A @ x_coeffs
        screen_y = A @ y_coeffs
        
        screen_points = np.column_stack([screen_x, screen_y])
        
        if len(screen_points) == 1:
            return screen_points[0]
        
        return screen_points
    
    def _make_json_serializable(self, obj):
        """Convert numpy arrays and other non-serializable objects to JSON-compatible format"""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(self._make_json_serializable(item) for item in obj)
        else:
            return obj

    def save_calibration(self):
        """Save calibration data with landmark-based mappings to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"landmark_eye_calibration_{timestamp}.json"
        calibration_data = {
            'transformation_matrix': self._make_json_serializable(self.transformation_matrix),
            'landmark_screen_mapping': self._make_json_serializable(self.landmark_screen_mapping),
            'screen_region_landmarks': self._make_json_serializable(self.screen_region_landmarks),
            'landmark_patterns': self._make_json_serializable(self.landmark_patterns),
            'calibration_points': self._make_json_serializable(self.calibration_points),
            'screen_resolution': [self.screen_w, self.screen_h],
            'timestamp': timestamp,
            'total_data_points': len(self.eye_data),
            'calibration_type': 'landmark_based',
            'mapping_quality': self._make_json_serializable(self._assess_mapping_quality())
        }
        try:
            services_dir = os.path.dirname(os.path.abspath(__file__))
            filepath = os.path.join(services_dir, filename)

            with open(filepath, 'w') as f:
                json.dump(calibration_data, f, indent=2)

            print(f"💾 Landmark-based calibration saved to: {filepath}")
            print(f"📊 Landmark mappings created: {len(self.landmark_screen_mapping)}")
            print(f"🗺️  Screen regions mapped: {len(self.screen_region_landmarks)}")
            return filepath

        except Exception as e:
            print(f"❌ Failed to save calibration: {e}")
            return None
    
    def _assess_mapping_quality(self):
        """Assess overall quality of landmark mappings"""
        if not self.landmark_screen_mapping:
            return 0.0
        
        qualities = []
        for mapping in self.landmark_screen_mapping.values():
            if 'quality_score' in mapping:
                qualities.append(mapping['quality_score'])
        
        if qualities:
            return {
                'average_quality': np.mean(qualities),
                'min_quality': np.min(qualities),
                'max_quality': np.max(qualities),
                'total_mappings': len(qualities)
            }
        else:
            return {'average_quality': 0.0}
    
    def load_calibration(self, filename):
        """Load existing calibration data"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            self.transformation_matrix = data['transformation_matrix']
            self.calibration_complete = True
            
            print(f"✅ Calibration loaded from: {filename}")
            print(f"📊 Accuracy: {self.transformation_matrix['accuracy']['total_rmse']:.1f} pixels RMSE")
            return True
            
        except Exception as e:
            print(f"❌ Error loading calibration: {e}")
            return False
    
    def collect_gaze_boundary_data(self, eye_pos, is_looking_at_screen=True):
        """Collect data for screen boundary detection"""
        data_point = {
            'eye_pos': eye_pos.copy(),
            'looking_at_screen': is_looking_at_screen,
            'timestamp': time.time()
        }
        
        if is_looking_at_screen:
            self.off_screen_gaze_data.append(data_point)
        else:
            self.off_screen_gaze_data.append(data_point)
    
    def is_gaze_within_screen_boundary(self, eye_pos):
        """Determine if current gaze is within screen viewing area"""
        if not self.transformation_matrix:
            return True 
        
        predicted_screen = self.apply_transformation(np.array(eye_pos))
        screen_x, screen_y = predicted_screen
        
        margin_x = self.screen_w * self.screen_boundary_margin
        margin_y = self.screen_h * self.screen_boundary_margin
        
        boundary_left = -margin_x
        boundary_right = self.screen_w + margin_x
        boundary_top = -margin_y
        boundary_bottom = self.screen_h + margin_y
        
        within_boundary = (boundary_left <= screen_x <= boundary_right and 
                          boundary_top <= screen_y <= boundary_bottom)
        
        return within_boundary
    
    def estimate_screen_engagement(self, eye_pos_history):
        """Estimate if user is engaged with laptop screen based on gaze patterns"""
        if len(eye_pos_history) < 10:
            return True 
        
        recent_positions = eye_pos_history[-10:]
        
        x_positions = [pos[0] for pos in recent_positions]
        y_positions = [pos[1] for pos in recent_positions]
        
        variance_x = np.var(x_positions)
        variance_y = np.var(y_positions)
        total_variance = variance_x + variance_y
        
        engagement_threshold = 50
        
        is_engaged = total_variance < engagement_threshold
        
        return is_engaged
    
    def is_valid_eye_data(self, eye_pos):
        """Validate eye position data to filter out outliers"""
        x, y = eye_pos
        
        if x < 0 or x > 1000 or y < 0 or y > 800:
            return False
        
        if x == 0 and y == 0:
            return False
        
        if not (np.isfinite(x) and np.isfinite(y)):
            return False
        
        return True
    
    def validate_point_data(self, point_data):
        """Validate stability of data collected for a calibration point"""
        if len(point_data) < 10:
            return False
        
        x_coords = [pos[0] for pos in point_data]
        y_coords = [pos[1] for pos in point_data]
        
        x_var = np.var(x_coords)
        y_var = np.var(y_coords)
        
        max_variance = 100
        
        return x_var < max_variance and y_var < max_variance
    
    def remove_outliers(self, eye_points, screen_points):
        """Remove outlier data points that could corrupt the calibration"""
        if len(eye_points) < 10:
            return eye_points, screen_points
        
        eye_points = np.array(eye_points)
        screen_points = np.array(screen_points)
        
        eye_median = np.median(eye_points, axis=0)
        screen_median = np.median(screen_points, axis=0)
        
        eye_distances = np.linalg.norm(eye_points - eye_median, axis=1)
        screen_distances = np.linalg.norm(screen_points - screen_median, axis=1)
        
        eye_threshold = np.percentile(eye_distances, 95) 
        screen_threshold = np.percentile(screen_distances, 95)
        
        valid_mask = (eye_distances <= eye_threshold) & (screen_distances <= screen_threshold)
        
        print(f"🔍 Outlier detection: removing {np.sum(~valid_mask)} of {len(eye_points)} points")
        
        return eye_points[valid_mask], screen_points[valid_mask]
    
    def draw_calibration_ui(self, frame):
        """Draw calibration UI on frame"""
        if self.calibration_complete:
            cv2.putText(frame, "CALIBRATION COMPLETE", (20, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, "Pure eye tracking active!", (20, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            return
        
        total_points = len(self.calibration_points)
        cv2.putText(frame, f"CALIBRATION: Point {self.current_point_index + 1}/{total_points}", 
                   (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        if self.current_point_index < len(self.calibration_points):
            target_x, target_y = self.calibration_points[self.current_point_index]
            
            if self.is_collecting:
                progress = self.collection_frames / self.frames_per_point
                cv2.putText(frame, f"COLLECTING... {progress*100:.0f}%", 
                           (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                cv2.putText(frame, f"Keep head still, look at target", 
                           (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            else:
                cv2.putText(frame, f"Look at target: ({target_x}, {target_y})", 
                           (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, "Press SPACE when ready", 
                           (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        cv2.putText(frame, "Only move your EYES!", (20, frame.shape[0] - 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, "ESC: Exit, R: Reset", (20, frame.shape[0] - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

def create_calibration_target_window():
    """Create a fullscreen window showing calibration target"""
    screen_w, screen_h = pyautogui.size()
    
    target_window = np.zeros((screen_h, screen_w, 3), dtype=np.uint8)
    
    cv2.namedWindow('Calibration Target', cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('Calibration Target', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    return target_window

def draw_target_point(window, position, active=True):
    """Draw calibration target point"""
    x, y = position
    
    if active:
        time_val = time.time()
        radius = int(20 + 10 * math.sin(time_val * 3))
        color = (0, 0, 255)  
    else:
        radius = 15
        color = (100, 100, 100) 
    
    cv2.circle(window, (x, y), radius, color, -1)
    cv2.circle(window, (x, y), radius + 5, (255, 255, 255), 2)
    
    cv2.line(window, (x-30, y), (x+30, y), (255, 255, 255), 2)
    cv2.line(window, (x, y-30), (x, y+30), (255, 255, 255), 2)

def run_pure_eye_calibration():
    """Run the pure eye movement calibration process with MediaPipe Face Mesh"""
    print("🎯 Starting Pure Eye Movement Calibration")
    print("📋 This will calibrate your eye movement for precise cursor control")
    print("👁️  Using MediaPipe Face Mesh for high-precision iris tracking")
    print("⚠️  IMPORTANT: Keep your head completely still during calibration!")
    
    calibrator = PureEyeCalibrator()
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    target_window = create_calibration_target_window()
    
    try:
        import mediapipe as mp
        
        mp_face_mesh = mp.solutions.face_mesh
        
        try:
            face_mesh = mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,     
                min_detection_confidence=0.3, 
                min_tracking_confidence=0.3  
            )
        except Exception as mp_error:
            error_msg = str(mp_error)
            print(f"❌ MediaPipe initialization failed: {error_msg}")
            if "Failed to parse" in error_msg or "node" in error_msg.lower():
                print("\n🔧 This is a MediaPipe version/compatibility issue.")
                print("   Try these solutions:")
                print("   1. Reinstall MediaPipe: pip uninstall mediapipe && pip install mediapipe")
                print("   2. Install specific version: pip install mediapipe==0.10.8")
                print("   3. Check Python version compatibility (MediaPipe requires Python 3.8-3.11)")
                print("   4. If using conda: conda install -c conda-forge mediapipe")
            raise Exception(f"MediaPipe initialization error: {error_msg}")
        
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles
        
        print("✅ MediaPipe Face Mesh with iris detection initialized")
        
    except ImportError:
        print("❌ MediaPipe not available!")
        print("   Install MediaPipe: pip install mediapipe")
        return None
    except Exception as e:
        print(f"❌ MediaPipe error: {e}")
        return None
        
    print("🎮 Controls:")
    print("   SPACE - Start collecting data for current target")
    print("   S - Skip calibration and use previous calibration file")
    print("   ESC - Cancel calibration")
    print("   Look at the RED target and press SPACE when ready")
    
    try:
        detection_failure_count = 0
        max_detection_failures = 5 
        last_successful_detection = time.time()
        
        while not calibrator.calibration_complete:
            ret, frame = cap.read()
            if not ret:
                continue
            try:
                if mirror_preview:
                    frame = cv2.flip(frame, 1)
            except Exception:
                pass
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_frame)
            
            face_detected = False
            if results.multi_face_landmarks and len(results.multi_face_landmarks) > 0:
                landmarks = results.multi_face_landmarks[0]
                if len(landmarks.landmark) >= 468: 
                    face_detected = True
                    detection_failure_count = 0
                    last_successful_detection = time.time()
            
            if not face_detected:
                detection_failure_count += 1
                time_since_last_detection = time.time() - last_successful_detection
                
                if time_since_last_detection < 2.0:  
                    face_detected = True
            
            target_window.fill(0)
            
            for i, point in enumerate(calibrator.calibration_points):
                active = (i == calibrator.current_point_index)
                draw_target_point(target_window, point, active)
            
            if calibrator.current_point_index < len(calibrator.calibration_points):
                cv2.putText(target_window, f"Look at the RED target", 
                           (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
                cv2.putText(target_window, f"Point {calibrator.current_point_index + 1} of {len(calibrator.calibration_points)}", 
                           (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                if calibrator.is_collecting:
                    progress = calibrator.collection_frames / calibrator.frames_per_point
                    cv2.putText(target_window, f"Collecting... {progress*100:.0f}%", 
                               (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                else:
                    cv2.putText(target_window, "Press SPACE when ready", 
                               (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                    cv2.putText(target_window, "Press S to skip and use previous calibration", 
                               (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            cv2.imshow('Calibration Target', target_window)
            
            if face_detected and results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0]
                h, w = frame.shape[:2]
                
                head_pos = calibrator.get_head_position(landmarks, w, h)
                eye_pos = calibrator.get_eye_position(landmarks, w, h)
                
                calibrator._current_landmark_signature = calibrator.extract_landmark_signature(landmarks, w, h)
                
                if calibrator.is_collecting:
                    head_moved = calibrator.check_head_movement(head_pos)
                    
                    if head_moved:
                        cv2.putText(frame, "HEAD MOVED! Keep still!", 
                                   (20, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                        calibrator.collection_frames = 0
                        calibrator.baseline_head_position = head_pos
                    else:
                        current_target = calibrator.calibration_points[calibrator.current_point_index]
                        calibrator.collect_calibration_point(eye_pos, current_target)
                
                eye_x, eye_y = int(eye_pos[0]), int(eye_pos[1])
                
                
                mp_drawing.draw_landmarks(
                    frame, landmarks, mp_face_mesh.FACEMESH_IRISES,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_iris_connections_style())
                
                eye_x, eye_y = int(eye_pos[0]), int(eye_pos[1])
                
                cv2.circle(frame, (eye_x, eye_y), 6, (0, 255, 0), -1)
                cv2.circle(frame, (eye_x, eye_y), 10, (0, 255, 0), 2)
                cv2.circle(frame, (eye_x, eye_y), 12, (255, 255, 255), 1)
                
                iris_landmarks = [469, 470, 471, 472, 474, 475, 476, 477]
                for idx in iris_landmarks:
                    if idx < len(landmarks.landmark):
                        point = landmarks.landmark[idx]
                        px, py = int(point.x * w), int(point.y * h)
                        cv2.circle(frame, (px, py), 3, (255, 255, 0), -1)
                
                left_eye_outline = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
                right_eye_outline = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
                
                left_points = []
                for idx in left_eye_outline:
                    if idx < len(landmarks.landmark):
                        point = landmarks.landmark[idx]
                        left_points.append([int(point.x * w), int(point.y * h)])
                
                if len(left_points) > 3:
                    left_points = np.array(left_points, dtype=np.int32)
                    cv2.polylines(frame, [left_points], True, (255, 0, 255), 1)
                
                right_points = []
                for idx in right_eye_outline:
                    if idx < len(landmarks.landmark):
                        point = landmarks.landmark[idx]
                        right_points.append([int(point.x * w), int(point.y * h)])
                
                if len(right_points) > 3:
                    right_points = np.array(right_points, dtype=np.int32)
                    cv2.polylines(frame, [right_points], True, (255, 0, 255), 1)
                
                cv2.putText(frame, "FULL FACE MESH TRACKING", 
                           (10, frame.shape[0] - 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.putText(frame, "Ultra-High Sensitivity Mode", 
                           (10, frame.shape[0] - 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                time_since_detection = time.time() - last_successful_detection
                if time_since_detection < 1.0:
                    cv2.putText(frame, "Detection: GOOD", 
                               (10, frame.shape[0] - 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                elif time_since_detection < 2.0:
                    cv2.putText(frame, "Detection: OK (grace period)", 
                               (10, frame.shape[0] - 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                else:
                    cv2.putText(frame, f"Detection lost {time_since_detection:.1f}s ago", 
                               (10, frame.shape[0] - 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            else:
                time_since_detection = time.time() - last_successful_detection
                if time_since_detection < 5.0:
                    cv2.putText(frame, f"Face detection lost {time_since_detection:.1f}s ago - adjust position", 
                               (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                else:
                    cv2.putText(frame, "No face detected - position yourself in view", 
                               (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                cv2.putText(frame, f"Failures: {detection_failure_count}", 
                           (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
            calibrator.draw_calibration_ui(frame)
            
            cv2.imshow('Camera Feed', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  
                print("Calibration cancelled")
                break
            elif key == ord('s') or key == ord('S'): 
                print("⏭️  Skipping calibration - looking for previous calibration file...")
                global latest_calibration_file
                
                import glob
                current_dir = os.getcwd()
                services_dir = os.path.dirname(os.path.abspath(__file__))
                
                search_dirs = [current_dir, services_dir]
                calibration_files = []
                
                for search_dir in search_dirs:
                    landmark_files = glob.glob(os.path.join(search_dir, "landmark_eye_calibration_*.json"))
                    traditional_files = glob.glob(os.path.join(search_dir, "pure_eye_calibration_*.json"))
                    calibration_files.extend(landmark_files + traditional_files)
                
                if calibration_files:
                    calibration_files.sort(key=os.path.getmtime, reverse=True)
                    latest_file = calibration_files[0]
                    print(f"✅ Found previous calibration: {os.path.basename(latest_file)}")
                    print(f"📂 Using calibration from: {latest_file}")
                    
                    latest_calibration_file = latest_file
                    
                    calibrator.calibration_complete = True
                    
                    target_window.fill(0)
                    cv2.putText(target_window, "CALIBRATION SKIPPED", 
                               (target_window.shape[1]//2 - 300, target_window.shape[0]//2 - 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 3)
                    cv2.putText(target_window, "Using previous calibration file", 
                               (target_window.shape[1]//2 - 250, target_window.shape[0]//2 + 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    cv2.putText(target_window, f"{os.path.basename(latest_file)}", 
                               (target_window.shape[1]//2 - 300, target_window.shape[0]//2 + 80), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    cv2.putText(target_window, "Press any key to continue", 
                               (target_window.shape[1]//2 - 200, target_window.shape[0]//2 + 140), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                    cv2.imshow('Calibration Target', target_window)
                    cv2.waitKey(2000) 
                    break
                else:
                    print("❌ No previous calibration file found!")
                    print("⚠️  You must complete calibration at least once.")
                    target_window.fill(0)
                    cv2.putText(target_window, "NO PREVIOUS CALIBRATION FOUND", 
                               (target_window.shape[1]//2 - 400, target_window.shape[0]//2), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
                    cv2.putText(target_window, "Please complete calibration", 
                               (target_window.shape[1]//2 - 250, target_window.shape[0]//2 + 60), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    cv2.imshow('Calibration Target', target_window)
                    cv2.waitKey(2000)
            elif key == ord(' '): 
                if not calibrator.is_collecting and calibrator.current_point_index < len(calibrator.calibration_points):
                    if face_detected and results.multi_face_landmarks:  
                        calibrator.is_collecting = True
                        calibrator.baseline_head_position = None
                        print(f"🎯 Starting collection for point {calibrator.current_point_index + 1}")
                    else:
                        time_since_detection = time.time() - last_successful_detection
                        if time_since_detection < 2.0:
                            print("⚠️  Detection temporarily lost - try again in a moment")
                        else:
                            print("⚠️  No face detected! Position yourself in camera view.")
            elif key == ord('r') or key == ord('R'): 
                calibrator.current_point_index = 0
                calibrator.collection_frames = 0
                calibrator.is_collecting = False
                calibrator.eye_data = []
                calibrator.screen_data = []
                calibrator.baseline_head_position = None
                print("🔄 Calibration reset")
        
        if calibrator.calibration_complete:
            print("🎉 Calibration completed successfully!")
            print("📄 Calibration file saved")
            print("🚀 You can now use pure eye tracking!")
            
            target_window.fill(0)
            cv2.putText(target_window, "CALIBRATION COMPLETE!", 
                       (target_window.shape[1]//2 - 300, target_window.shape[0]//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
            cv2.putText(target_window, "You can now use pure eye tracking", 
                       (target_window.shape[1]//2 - 250, target_window.shape[0]//2 + 80), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(target_window, "Press any key to exit", 
                       (target_window.shape[1]//2 - 150, target_window.shape[0]//2 + 140), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            cv2.imshow('Calibration Target', target_window)
            cv2.waitKey(0)
        
    except ImportError:
        print("❌ MediaPipe not available. Please install MediaPipe first.")
    
    except Exception as e:
        print(f"❌ Error during calibration: {e}")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()

    try:
        if latest_calibration_file:
            return latest_calibration_file
    except Exception:
        pass

    try:
        if 'calibrator' in locals() and hasattr(calibrator, 'saved_filename'):
            return calibrator.saved_filename
    except Exception:
        pass

    return None

if __name__ == "__main__":
    run_pure_eye_calibration()
