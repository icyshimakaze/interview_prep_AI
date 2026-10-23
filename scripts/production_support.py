"""Ephemeral TLS and loopback-only ingress used by the production verification runner."""

import ssl
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from ipaddress import ip_address
from pathlib import Path

import httpx
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

HOP_HEADERS = {
    "connection",
    "transfer-encoding",
    "keep-alive",
    "content-length",
    "content-encoding",
}


def generate_certificates(directory: Path) -> None:
    """Create a private throwaway CA and host certificate, never install it system-wide."""
    directory.mkdir(parents=True, exist_ok=False)
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Local production check CA")])
    now = datetime.now(UTC)
    ca = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .sign(ca_key, hashes.SHA256())
    )
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")]))
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.DNSName("localhost"),
                    x509.DNSName("host.docker.internal"),
                    x509.IPAddress(ip_address("127.0.0.1")),
                ]
            ),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )
    (directory / "ca.pem").write_bytes(ca.public_bytes(serialization.Encoding.PEM))
    (directory / "server.pem").write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    (directory / "server.key").write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )


@contextmanager
def tls_gateway(
    port: int, upstream_port: int, certificates: Path, *, vercel: bool
) -> Iterator[None]:
    """Model TLS termination and Vercel's overwritten IP header on loopback only."""

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            pass  # No URLs, headers or request bodies in local gateway logs.

        def forward(self) -> None:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 <= size <= 16 * 1024 * 1024:
                self.send_error(413)
                return
            headers = {
                k: v for k, v in self.headers.items() if k.lower() not in HOP_HEADERS | {"host"}
            }
            headers["accept-encoding"] = "identity"
            if vercel:
                headers["x-vercel-forwarded-for"] = self.client_address[0]
            with httpx.Client(timeout=45, trust_env=False) as client:
                result = client.request(
                    self.command,
                    f"http://127.0.0.1:{upstream_port}{self.path}",
                    content=self.rfile.read(size),
                    headers=headers,
                )
            self.send_response(result.status_code)
            for key, value in result.headers.multi_items():
                if key.lower() not in HOP_HEADERS:
                    self.send_header(key, value)
            self.send_header("Content-Length", str(len(result.content)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(result.content)

        do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = do_HEAD = forward

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certificates / "server.pem", certificates / "server.key")
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
