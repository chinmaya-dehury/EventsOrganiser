import aiohttp
import random
import jwt
from OpenSSL import crypto
from datetime import timedelta

def generate_selfsigned_cert(expires_in: timedelta = timedelta(days=8)) -> tuple[int, bytes, bytes]:
    """
    Generate a self signed certificate to be used for Microsoft Graph rich notifications
    
    :return: A tuple of serial number, certificate and key
    """
    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_RSA, 2048)
    serial_nr = random.randint(100000, 730750818665451459101842416358141509827966271488)

    x509 = crypto.X509()
    x509.set_version(2)
    x509.set_pubkey(pkey)
    x509.set_serial_number(serial_nr)
    x509.gmtime_adj_notBefore(0)
    x509.gmtime_adj_notAfter(int(expires_in.total_seconds()))

    x509.sign(pkey, 'SHA256')

    return (
        serial_nr,
        crypto.dump_certificate(crypto.FILETYPE_PEM, x509),
        crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey)
    )