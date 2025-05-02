const nodes = new vis.DataSet();
const edges = new vis.DataSet();

const container = document.getElementById('network');
const data = { nodes, edges };
const options = {
  nodes: {
    shape: 'dot',
    size: 20,
    font: { color: '#000' }
  },
  edges: {
    arrows: { to: { enabled: false } },  
    smooth: { type: 'continuous' },     
    color: { color: '#000000' },        
    width: 2,                           
    hoverWidth: 3                       
  }
};
const network = new vis.Network(container, data, options);
let selectedNode = null;

network.on("click", function (params) {
  if (params.nodes.length === 1) {
    const clickedNode = params.nodes[0];

    if (!selectedNode) {
      selectedNode = clickedNode;
      nodes.update({ id: clickedNode, color: { background: '#FFA500' } });
    } else if (selectedNode !== clickedNode) {
      const weight = prompt(`Enter weight for edge between ${selectedNode} → ${clickedNode}:`);
      const parsedWeight = parseInt(weight);

      if (!isNaN(parsedWeight)) {
        fetch('/add_edge', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ source: selectedNode, target: clickedNode, weight: parsedWeight })
        })
        .then(res => res.json())
        .then(() => {
          const edgeId = `${selectedNode}-${clickedNode}`;
          
          edges.add({ id: edgeId, from: selectedNode, to: clickedNode, label: String(parsedWeight) });

          nodes.update({ id: selectedNode, color: { background: '#97C2FC' } });
          selectedNode = null;
        });
      } else {
        alert("Invalid weight.");
        nodes.update({ id: selectedNode, color: { background: '#97C2FC' } });
        selectedNode = null;
      }
    } else {
      nodes.update({ id: selectedNode, color: { background: '#97C2FC' } });
      selectedNode = null;
    }
  }
});

function resetColors() {
  nodes.get().forEach(node => {
    nodes.update({ id: node.id, color: { background: '#97C2FC' } });
  });

  edges.get().forEach(edge => {
    edges.update({ id: edge.id, color: '#848484' });
  });
}

function highlightPath(path) {
  resetColors();

  path.forEach(nodeId => {
    nodes.update({ id: nodeId, color: { background: '#FFD700' } });
  });

  for (let i = 0; i < path.length - 1; i++) {
    const from = path[i];
    const to = path[i + 1];

    const match = edges.get().find(e => e.from === from && e.to === to);
    if (match) {
      edges.update({ id: match.id, color: '#FFD700' });
    }
  }
}

function addRouter() {
  const name = document.getElementById('routerName').value.trim();
  if (!name) return alert("Enter a valid router name.");

  fetch('/add_router', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name })
  })
  .then(res => res.json())
  .then(() => {
    nodes.add({ id: name, label: name });
    document.getElementById('routerName').value = '';
  });
}

function addEdge() {
  const source = document.getElementById('source').value.trim();
  const target = document.getElementById('target').value.trim();
  const weight = parseInt(document.getElementById('weight').value.trim());

  if (!source || !target || isNaN(weight)) return alert("Provide valid edge details.");

  fetch('/add_edge', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source, target, weight })
  })
  .then(res => res.json())
  .then(() => {
    const edgeId = `${source}-${target}`;
    edges.add({ id: edgeId, from: source, to: target, label: String(weight) });
    document.getElementById('source').value = '';
    document.getElementById('target').value = '';
    document.getElementById('weight').value = '';
  });
}

function findShortestPath() {
  const start = document.getElementById('startNode').value.trim();
  const end = document.getElementById('endNode').value.trim();

  fetch('/shortest_path', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ start, end })
  })
  .then(res => res.json())
  .then(result => {
    if (result.path) {
      highlightPath(result.path);
      alert(`Shortest path: ${result.path.join(' → ')}\nDistance: ${result.distance}`);
    } else {
      alert(result.message || "Path not found.");
    }
  });
}

function resetSelection() {
  if (selectedNode) {
    nodes.update({ id: selectedNode, color: { background: '#97C2FC' } });
    selectedNode = null;
  }
}

function logLayerAction(message) {
  const logContainer = document.getElementById('layer-log');
  const newLogEntry = document.createElement('div');
  newLogEntry.innerText = message;
  logContainer.appendChild(newLogEntry);
  logContainer.scrollTop = logContainer.scrollHeight;
}

function openLayerModal() {
  const modal = document.getElementById('layer-modal');
  modal.style.display = "block";
}

function closeLayerModal() {
  const modal = document.getElementById('layer-modal');
  modal.style.display = "none";
}

document.getElementById('close-modal').addEventListener('click', closeLayerModal);

function sendMessage() {
  const src = document.getElementById('msgSrc').value.trim();
  const dest = document.getElementById('msgDest').value.trim();
  const message = document.getElementById('msgText').value.trim();

  if (!src || !dest || !message) {
    alert("Please fill in all the fields.");
    return;
  }

  fetch('/send_message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ src, dest, message })
  })
  .then(res => res.json())
  .then(data => {
    const modal = document.getElementById('layer-modal');
    const layerLog = document.getElementById('layer-log');

    layerLog.innerHTML = '';

    layerLog.innerHTML += `<p><strong>Shortest Path:</strong> ${Array.isArray(data.path) ? data.path.join(' -> ') : 'No path found'}</p>`;

    layerLog.innerHTML += `<p><strong>Encoded Message:</strong> ${data.encodedMessage}</p>`;

    layerLog.innerHTML += `<p><strong>Decoded Message:</strong> ${data.received_message}</p>`;


    layerLog.innerHTML += `<p><strong>At sender</strong></p>`;
    layerLog.innerHTML += `<p><strong>[Application layer]</strong> Encrypted and sending: ${data.encodedMessage}</p>`;
    layerLog.innerHTML += `<p><strong>[Transport layer]</strong> Segmented into ${data.sender_data.number_of_segments} parts</p>`;
    layerLog.innerHTML += `<p><strong>[Network layer]</strong> IP ${data.sender_data.source_ip} -> ${data.sender_data.dest_ip}</p>`;
    layerLog.innerHTML += `<p><strong>[Data link layer]</strong> MAC ${data.sender_data.source_mac} -> ${data.sender_data.dest_mac}</p>`;
    layerLog.innerHTML += `<p><strong>[Physical layer]</strong> Converted to bit stream and transmitted</p>`;

    layerLog.innerHTML += `<p><strong>At receiver</strong></p>`;
    layerLog.innerHTML += `<p><strong>[Physical layer]</strong> Received and decoded bits</p>`;
    layerLog.innerHTML += `<p><strong>[Data link layer]</strong> MAC verified</p>`;
    layerLog.innerHTML += `<p><strong>[Network layer]</strong> TTL now ${data.ttl}, continuing</p>`;
    layerLog.innerHTML += `<p><strong>[Transport layer]</strong> Reassembled segments</p>`;
    layerLog.innerHTML += `<p><strong>[Application layer]</strong> Decypted and received : ${data.message}</p>`;
    
    modal.style.display = "block";

    document.getElementById('close-modal').onclick = function() {
      modal.style.display = "none";
    };
  })
  .catch(error => {
    console.error('Error:', error);
    alert('There was an issue with sending the message. Please try again.');
  });
}

window.onload = () => {
  Promise.all([
    fetch('/add_router', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: "Sender" })
    }),
    fetch('/add_router', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: "Receiver" })
    })
  ]).then(() => {
    fetch('/get_data')
      .then(res => res.json())
      .then(data => {
        data.routers.forEach(r => {
          if (!nodes.get(r)) nodes.add({ id: r, label: r });
        });
        data.edges.forEach(e => {
          const edgeId = `${e.from}-${e.to}`;
          edges.add({ id: edgeId, from: e.from, to: e.to, label: String(e.weight) });
        });
      });
  });
};