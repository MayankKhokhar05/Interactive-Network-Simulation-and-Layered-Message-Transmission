import random

class ApplicationLayer:
    def __init__(self, key=3):
        self.key = key

    def encrypt(self, text):
        return ''.join(chr((ord(c) + self.key) % 256) for c in text)

    def decrypt(self, text):
        return ''.join(chr((ord(c) - self.key) % 256) for c in text)

    def send(self, data):
        encrypted_data = self.encrypt(data)
        print(f"[Application] Encrypted and sending: {encrypted_data}")
        return {"data": encrypted_data}

    def receive(self, packet):
        decrypted_data = self.decrypt(packet["data"])
        print(f"[Application] Decrypted and received: {decrypted_data}")
        return decrypted_data


class TransportLayer:
    def __init__(self, source_port=1234, dest_port=80):
        self.source_port = source_port
        self.dest_port = dest_port

    def segment(self, data):
        return [data[i:i+5] for i in range(0, len(data), 5)]

    def reassemble(self, segments):
        return ''.join(segments)

    def send(self, packet):
        segments = self.segment(packet["data"])
        packet.update({
            "segments": segments,
            "source_port": self.source_port,
            "dest_port": self.dest_port,
            "number_of_segments": len(segments)
        })
        del packet["data"]
        print(f"[Transport] Segmented data into {len(segments)} parts")
        return packet

    def receive(self, packet):
        reassembled = self.reassemble(packet["segments"])
        print(f"[Transport] Reassembled segments")
        packet["data"] = reassembled
        return packet


class NetworkLayer:
    def __init__(self, source_ip="192.168.0.1", dest_ip="192.168.0.2", ttl=5):
        self.source_ip = source_ip
        self.dest_ip = dest_ip
        self.ttl = ttl

    def send(self, packet):
        packet.update({
            "source_ip": self.source_ip,
            "dest_ip": self.dest_ip,
            "ttl": self.ttl
        })
        print(f"[Network] IP {self.source_ip} -> {self.dest_ip}, TTL = {self.ttl}")
        return packet

    def receive(self, packet):
        packet["ttl"] -= 1
        if packet["ttl"] <= 0:
            raise Exception("[Network] Packet dropped: TTL expired")
        print(f"[Network] TTL now {packet['ttl']}, continuing...")
        return packet


class DataLinkLayer:
    def __init__(self, source_mac="AA:BB:CC:DD:EE:01", dest_mac="AA:BB:CC:DD:EE:02"):
        self.source_mac = source_mac
        self.dest_mac = dest_mac

    def send(self, packet):
        packet.update({
            "source_mac": self.source_mac,
            "dest_mac": self.dest_mac,
            "fcs": "ok" 
        })
        print(f"[DataLink] MAC {self.source_mac} -> {self.dest_mac}")
        return packet

    def receive(self, packet):
        if packet["dest_mac"] != self.source_mac:
            raise Exception("[DataLink] MAC mismatch! Packet dropped.")
        print(f"[DataLink] MAC verified.")
        return packet


class PhysicalLayer:
    def __init__(self, reliability=0.99):
        self.reliability = reliability

    def send(self, packet):
        bits = str(packet).encode('utf-8')
        if random.random() > self.reliability:
            raise Exception("[Physical] Signal lost during transmission.")
        print(f"[Physical] Bits transmitted.")
        return bits

    def receive(self, bits):
        packet = eval(bits.decode('utf-8'))
        print(f"[Physical] Bits received and decoded.")
        return packet
