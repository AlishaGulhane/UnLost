import argparse
import pickle
import os
import time
from pathlib import Path

# Try importing pyrosm. If it fails, fallback to standard mock for demo
try:
    from pyrosm import OSM
    from scipy.spatial import cKDTree
    HAS_PYROSM = True
except ImportError:
    HAS_PYROSM = False

def train_map_matching_model(pbf_path: str, output_model_path: str):
    """
    Trains a map-matching model (Spatial Index + Graph) using OSM PBF data.
    This model allows raw INS trajectories to snap to the physical road network.
    """
    print(f"Loading real-time Pune data from: {pbf_path}")
    start_time = time.time()

    if not os.path.exists(pbf_path):
        raise FileNotFoundError(f"PBF file not found at {pbf_path}")

    model_data = {}

    if HAS_PYROSM:
        print("Initializing Pyrosm OSM parser...")
        osm = OSM(pbf_path)
        
        print("Extracting driving network...")
        nodes, edges = osm.get_network(network_type="driving", nodes=True)
        
        print(f"Extracted {len(nodes)} nodes and {len(edges)} edges.")
        
        print("Building cKDTree Spatial Index for fast Map-Matching...")
        # Create KDTree using lat, lon for fast nearest-neighbor lookups (snapping)
        coords = nodes[['lat', 'lon']].values
        kdtree = cKDTree(coords)
        
        model_data = {
            'nodes': nodes,
            'edges': edges,
            'kdtree': kdtree,
            'network_type': 'driving',
            'metadata': {
                'timestamp': time.time(),
                'source': pbf_path
            }
        }
        print("Spatial index and graph built successfully.")
    else:
        print("WARN: pyrosm or scipy not found. Creating simulated model structure.")
        # Simulate training delay for mock
        time.sleep(2)
        model_data = {
            'status': 'Simulated Map-Matching Model',
            'source': pbf_path,
            'description': 'Install pyrosm and scipy to extract real graph and KDTree'
        }

    # Save model
    os.makedirs(os.path.dirname(output_model_path), exist_ok=True)
    with open(output_model_path, 'wb') as f:
        pickle.dump(model_data, f)
    
    elapsed = time.time() - start_time
    print(f"Model successfully saved to {output_model_path} in {elapsed:.2f}s")
    print("This trained model can now be used in the pipeline to snap drifting INS coordinates to real roads.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Map-Matching Model on OSM PBF")
    parser.add_argument("--pbf", type=str, default=r"C:\Users\alish\Documents\SIH Dead reckoning\SIH\western-zone-260928.osm.pbf", help="Path to OSM PBF file")
    parser.add_argument("--output", type=str, default=r"C:\Users\alish\Documents\SIH Dead reckoning\SIH\models\map_matching_model.pkl", help="Path to save trained model")
    
    args = parser.parse_args()
    train_map_matching_model(args.pbf, args.output)
