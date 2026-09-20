import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class OllamaMockHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/chat":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            
            model = data.get("model", "")
            messages = data.get("messages", [])
            user_msg = messages[-1]["content"] if messages else ""
            
            # Extract retrieved context and generate grounded answer
            if "PX-7788" in user_msg or "8.5 bar" in user_msg or "11 bar" in user_msg:
                answer = "Based on [test_equipment_px7788.pdf, Page 1], the maximum allowable pressure for equipment PX-7788 is 11 bar."
            elif "LOTO" in user_msg or "shutdown" in user_msg or "85.0°C" in user_msg:
                answer = "According to [NOVA_Safety_SOP_LOTO.txt, Page 1], immediate emergency shutdown is strictly required if pump operating temperature exceeds 85.0°C or vibration exceeds 4.5 mm/s RMS."
            else:
                answer = f"Based on the provided context: {user_msg[:100]}"

            response_data = {
                "model": model or "gemma4:latest",
                "created_at": "2026-09-14T20:30:00Z",
                "message": {
                    "role": "assistant",
                    "content": answer
                },
                "done": True,
                "total_duration": 15000000,
                "eval_duration": 12000000
            }
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port=11434):
    server_address = ('localhost', port)
    httpd = HTTPServer(server_address, OllamaMockHandler)
    print(f"Mock Ollama server listening on http://localhost:{port}/api/chat...")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
