from network_layers import *

class Sender:
    def __init__(self):
        self.app = ApplicationLayer()
        self.trans = TransportLayer()
        self.net = NetworkLayer()
        self.link = DataLinkLayer()
        self.phys = PhysicalLayer()

    def send(self, data, path):
        packet = self.app.send(data)
        packet = self.trans.send(packet)
        packet = self.net.send(packet)
        packet['route'] = path
        for hop in path:
            print(f"[Router] Hopping through {hop}")
        packet = self.link.send(packet)
        bits = self.phys.send(packet)
        return bits

class Receiver:
    def __init__(self):
        self.app = ApplicationLayer()
        self.trans = TransportLayer()
        self.net = NetworkLayer(source_ip="192.168.0.2", dest_ip="192.168.0.1")
        self.link = DataLinkLayer(source_mac="AA:BB:CC:DD:EE:02", dest_mac="AA:BB:CC:DD:EE:01")
        self.phys = PhysicalLayer()

    def receive(self, bits):
        packet = self.phys.receive(bits)
        packet = self.link.receive(packet)
        packet = self.net.receive(packet)
        packet = self.trans.receive(packet)
        return self.app.receive(packet)

def run_simulation(user_input, path):
    sender = Sender()
    receiver = Receiver()
    bits = sender.send(user_input, path)
    message = receiver.receive(bits)
    return message
