from flask import Flask, render_template, request, jsonify
import networkx as nx
import random
from datetime import datetime

app = Flask(__name__)

# Create building graph with weights
building = nx.Graph()

# Nodes represent locations (rooms, corridors, exits)
locations = {
    'Room101': (50, 150), 'Room102': (250, 150), 'Room103': (450, 150),
    'Corridor1': (150, 150), 'Corridor2': (350, 150), 'Corridor3': (550, 150),
    'Staircase1': (150, 300), 'Staircase2': (550, 300),
    'Lobby': (350, 450), 'MainExit': (350, 550), 'FireExit': (150, 550)
}

# Add nodes with positions
for node, pos in locations.items():
    building.add_node(node, pos=pos)

# Add edges with initial weights
edges = [
    ('Room101', 'Corridor1', 1), ('Room102', 'Corridor2', 1), ('Room103', 'Corridor3', 1),
    ('Corridor1', 'Corridor2', 2), ('Corridor2', 'Corridor3', 2),
    ('Corridor1', 'Staircase1', 1), ('Corridor3', 'Staircase2', 1),
    ('Staircase1', 'Lobby', 3), ('Staircase2', 'Lobby', 3),
    ('Lobby', 'MainExit', 1), ('Lobby', 'FireExit', 2)
]

for edge in edges:
    building.add_edge(edge[0], edge[1], weight=edge[2])

# Simulate dynamic conditions
def update_weights():
    """Simulate changing conditions (crowds, hazards)"""
    for u, v, d in building.edges(data=True):
        # Random weight changes to simulate dynamic conditions
        base_weight = 1 if 'Room' in u or 'Room' in v else 2
        crowd_factor = random.uniform(0.8, 1.5)
        hazard_factor = 1.0
        
        # Simulate occasional hazards (10% chance)
        if random.random() < 0.1:
            hazard_factor = random.uniform(2, 5)
            
        d['weight'] = base_weight * crowd_factor * hazard_factor
        d['hazard'] = hazard_factor > 1.5

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_path', methods=['POST'])
def get_path():
    data = request.json
    start = data['start']
    
    # Update weights to reflect current conditions
    update_weights()
    
    # Find shortest path to nearest exit
    exits = ['MainExit', 'FireExit']
    paths = {}
    
    for exit_node in exits:
        try:
            path = nx.dijkstra_path(building, start, exit_node, weight='weight')
            cost = nx.dijkstra_path_length(building, start, exit_node, weight='weight')
            paths[exit_node] = {'path': path, 'cost': cost}
        except nx.NetworkXNoPath:
            continue
    
    if not paths:
        return jsonify({'error': 'No path to exit found'}), 404
    
    # Select the best path (lowest cost)
    best_exit = min(paths.keys(), key=lambda x: paths[x]['cost'])
    best_path = paths[best_exit]
    
    # Get edge status for visualization
    path_edges = list(zip(best_path['path'][:-1], best_path['path'][1:]))
    edge_status = []
    
    for u, v in path_edges:
        edge_data = building.get_edge_data(u, v)
        edge_status.append({
            'hazard': edge_data['hazard'],
            'weight': edge_data['weight']
        })
    
    return jsonify({
        'path': best_path['path'],
        'cost': best_path['cost'],
        'exit': best_exit,
        'edge_status': edge_status,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    })

@app.route('/trigger_alert', methods=['POST'])
def trigger_alert():
    # In a real system, this would notify authorities
    return jsonify({
        'status': 'success',
        'message': 'Emergency alert sent to authorities',
        'timestamp': datetime.now().strftime('%H:%M:%S')
    })

if __name__ == '__main__':
    app.run(debug=True)