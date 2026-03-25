#!/bin/sh
set -e

echo "[nac] freeradius bootstrap (permission-safe) starting..."

SECRET_RAW="${RADIUS_SHARED_SECRET:-}"
SECRET="$(printf %s "$SECRET_RAW" | tr -d '\r')"

if [ -z "$SECRET" ]; then
  echo "[nac] ERROR: RADIUS_SHARED_SECRET is required" >&2
  exit 1
fi

# Config dosyaları Windows bind-mount'ta "globally writable" görünebiliyor.
# FreeRADIUS bu durumda başlamayı reddediyor. Çözüm:
# - repo config'i /etc/freeradius/custom altına mount et
# - burada container FS içine kopyala ve chmod ile sıkılaştır

SRC="/etc/freeradius/custom"

install -d /etc/freeradius/mods-enabled /etc/freeradius/sites-enabled

# clients.conf: secret'i env'den okumak yerine burada "materialize" ediyoruz.
# Neden: Windows .env / env var sonuna \r sızınca FreeRADIUS "invalid Message-Authenticator" ile paketleri drop ediyor.
cat > /etc/freeradius/clients.conf <<EOF
# Generated at container start by bootstrap.sh

client localhost {
  ipaddr = 127.0.0.1
  proto = *
  secret = $SECRET
}

client docker_bridge {
  ipaddr = 172.18.0.0/16
  proto = *
  secret = $SECRET
}
EOF
chmod 640 /etc/freeradius/clients.conf

cp "$SRC/mods-enabled/rest" /etc/freeradius/mods-enabled/rest
chmod 640 /etc/freeradius/mods-enabled/rest

cp "$SRC/sites-enabled/default" /etc/freeradius/sites-enabled/default
chmod 640 /etc/freeradius/sites-enabled/default

echo "[nac] freeradius starting..."
if [ "${FREERADIUS_DEBUG:-0}" = "1" ]; then
  exec freeradius -X
fi

exec freeradius -f

