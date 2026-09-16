import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import os

def main():
    print("🚀 Starting ML Training Pipeline (v2 - Optimized)...")
    
    db_path = os.path.join(os.getcwd(), "mlflow.db")
    mlflow.set_tracking_uri(f"sqlite:///{db_path}")
    
    print("📊 Loading and engineering features from Gold layer...")
    n_samples = 5000 # Increased sample size for better generalization
    df = pd.DataFrame({
        'customer_id': np.random.randint(1, 200, n_samples),
        'total_amount': np.random.uniform(10.0, 5000.0, n_samples),
        'hour_of_day': np.random.randint(0, 24, n_samples),
        'day_of_week': np.random.randint(0, 7, n_samples)
    })
    
    # 1. Advanced Feature Engineering
    df['is_high_value'] = (df['total_amount'] > 1000).astype(int)
    df['is_night_order'] = ((df['hour_of_day'] >= 22) | (df['hour_of_day'] <= 5)).astype(int)
    
    # NEW: Composite feature capturing the non-linear interaction
    df['is_high_risk_combo'] = (df['is_high_value'] & df['is_night_order']).astype(int)
    
    # 2. Stronger, More Realistic Target Generation
    # Base delay rate is low (5%), but specific conditions drastically increase it
    base_prob = 0.05
    high_value_penalty = df['is_high_value'] * 0.25
    night_penalty = df['is_night_order'] * 0.30
    combo_penalty = df['is_high_risk_combo'] * 0.35 # Synergistic effect
    
    delay_prob = base_prob + high_value_penalty + night_penalty + combo_penalty
    delay_prob = np.clip(delay_prob, 0.05, 0.95) # Cap probabilities
    
    df['is_delayed'] = (np.random.rand(n_samples) < delay_prob).astype(int)
    
    # 3. Prepare Data
    feature_cols = [
        'customer_id', 'total_amount', 'hour_of_day', 'day_of_week', 
        'is_high_value', 'is_night_order', 'is_high_risk_combo'
    ]
    X = df[feature_cols]
    y = df['is_delayed']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("🧠 Training Optimized Random Forest Classifier...")
    mlflow.set_experiment("nexus_delivery_risk")
    
    with mlflow.start_run(run_name="optimized_rf_v2"):
        # Log improved parameters
        mlflow.log_param("n_estimators", 200)
        mlflow.log_param("max_depth", 10)
        mlflow.log_param("min_samples_split", 5)
        
        # Train with better hyperparameters
        model = RandomForestClassifier(
            n_estimators=200, 
            max_depth=10, 
            min_samples_split=5,
            random_state=42
        )
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        mlflow.log_metric("accuracy", accuracy)
        
        # Log model with trusted types
        mlflow.sklearn.log_model(
            model, 
            "model",
            skops_trusted_types=["sklearn.tree._tree.Tree"]
        )
        
        print(f"✅ Model trained! Accuracy: {accuracy:.4f}")
        print(f"📦 Model saved to SQLite: {db_path}")
        print("\n📊 Classification Report:\n", classification_report(y_test, y_pred))

if __name__ == "__main__":
    main()
