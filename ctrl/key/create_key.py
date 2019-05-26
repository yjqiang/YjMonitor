import rsa


pubkey_name = 'pubkey'
privkey_name = 'privkey'

pubkey, privkey = rsa.newkeys(1024)


with open(f'{pubkey_name}.pem', 'wb') as f:
    f.write(pubkey.save_pkcs1())

with open(f'{privkey_name}.pem', 'wb') as f:
    f.write(privkey.save_pkcs1())

