from flask import Flask, render_template, request, jsonify
from network_layers import ApplicationLayer, TransportLayer, NetworkLayer, DataLinkLayer, PhysicalLayer
from collections import defaultdict
import heapq

app = Flask(__name__)

routers = {}
edges = defaultdict(list)

class Sender:
    def __init__(self, src_ip, dest_ip, src_mac, dest_mac):
        self.app = ApplicationLayer()
        self.trans = TransportLayer()
        self.net = NetworkLayer(source_ip=src_ip, dest_ip=dest_ip)
        self.datalink = DataLinkLayer(source_mac=src_mac, dest_mac=dest_mac)
        self.phys = PhysicalLayer()

    def send(self, message):
        print("\n--- Sending Message ---")

        packet = self.app.send(message)
        packet = self.trans.send(packet)  
        packet = self.net.send(packet)
        packet = self.datalink.send(packet)
        bits = self.phys.send(packet)
        
        sender_metadata = {
            'bits' : bits,
            'packet': packet,
        }
        
        return sender_metadata



class Receiver:
    def __init__(self, own_ip, own_mac):
        self.app = ApplicationLayer()
        self.trans = TransportLayer()
        self.net = NetworkLayer(source_ip="", dest_ip=own_ip)
        self.datalink = DataLinkLayer(source_mac=own_mac, dest_mac=own_mac)
        self.phys = PhysicalLayer()

    def receive(self, bits):
        print("\n--- Receiving Message ---")
        packet = self.phys.receive(bits)
        packet = self.datalink.receive(packet)
        packet = self.net.receive(packet)
        packet = self.trans.receive(packet)
        message = self.app.receive(packet)
        
        receiver_metadata = {
            'message' : message,
            'ttl' : self.net.ttl
        }

        return receiver_metadata


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_router', methods=['POST'])
def add_router():
    name = request.json.get('name')
    if name and name not in routers:
        routers[name] = {}
        return jsonify({'message': 'Router added successfully'})
    return jsonify({'message': 'Router already exists or invalid'}), 400

@app.route('/add_edge', methods=['POST'])
def add_edge():
    source = request.json.get('source')
    target = request.json.get('target')
    weight = int(request.json.get('weight', 1))

    if source in routers and target in routers:
        edges[source].append((target, weight))
        edges[target].append((source, weight))
        return jsonify({'message': 'Edge added successfully'})
    return jsonify({'message': 'Invalid nodes'}), 400

@app.route('/get_data', methods=['GET'])
def get_data():
    return jsonify({
        'routers': list(routers.keys()),
        'edges': [
            {'from': src, 'to': tgt, 'weight': w}
            for src, neighbors in edges.items()
            for tgt, w in neighbors if src < tgt
        ]
    })

@app.route('/shortest_path', methods=['POST'])
def shortest_path():
    start = request.json.get('start')
    end = request.json.get('end')

    dist, prev = dijkstra(start)
    path = []
    at = end
    while at in prev:
        path.append(at)
        at = prev[at]
    if at == start:
        path.append(start)
        path.reverse()
        return jsonify({'path': path, 'distance': dist[end]})
    return jsonify({'message': 'No path found'}), 404

def dijkstra(start):
    dist = {node: float('inf') for node in routers}
    prev = {}
    dist[start] = 0
    heap = [(0, start)]

    while heap:
        current_dist, current = heapq.heappop(heap)
        if current_dist > dist[current]:
            continue
        for neighbor, weight in edges[current]:
            alt = current_dist + weight
            if alt < dist[neighbor]:
                dist[neighbor] = alt
                prev[neighbor] = current
                heapq.heappush(heap, (alt, neighbor))
    return dist, prev

@app.route('/send_message', methods=['POST'])
def send_message():
    src = request.json.get('src')
    dest = request.json.get('dest')
    message = request.json.get('message')

    if src not in routers or dest not in routers:
        return jsonify({'message': 'Invalid source or destination'}), 400

    dist, prev = dijkstra(src)
    if dest not in prev:
        return jsonify({'message': 'No path exists'}), 404

    path = []
    at = dest
    pathlen = 0
    while at in prev:
        path.append(at)
        at = prev[at]
        pathlen+=1
    path.append(src)
    path.reverse()

    src_ip = f"192.168.1.{list(routers.keys()).index(src)+1}"
    dest_ip = f"192.168.1.{list(routers.keys()).index(dest)+1}"
    src_mac = f"AA:BB:CC:DD:EE:{list(routers.keys()).index(src)+1:02d}"
    dest_mac = f"AA:BB:CC:DD:EE:{list(routers.keys()).index(dest)+1:02d}"

    sender = Sender(src_ip, dest_ip, src_mac, dest_mac)
    receiver = Receiver(dest_ip, dest_mac)

    layer_logs = [
        f"Application Layer: Message encrypted: {message}",
        f"Transport Layer: Segmentation complete.",
        f"Network Layer: Routing done from {src} to {dest}.",
        f"Data Link Layer: MAC address added ({src_mac} -> {dest_mac}).",
        f"Physical Layer: Bits transmitted over the network."
    ]

    try:
        encoded = sender.send(message)
        decoded = receiver.receive(encoded['bits'])
    except Exception as e:
        return jsonify({'message': str(e)}), 500

    encoded_message = str(encoded['packet']['segments'])

    return jsonify({
        'path': path,
        'message' : message,
        'encodedMessage': encoded_message,
        'sender_data' : encoded['packet'],
        'received_message' : decoded['message'],
        'ttl' : decoded['ttl'] - pathlen
    })


if __name__ == '__main__':
    app.run(debug=True)
