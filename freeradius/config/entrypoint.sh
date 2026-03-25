#!/bin/sh
echo "[nac] freeradius bootstrap starting..."

if [ -z "${RADIUS_SHARED_SECRET:-}" ]; then
  echo "[nac] ERROR: RADIUS_SHARED_SECRET is required" >&2
  exit 1
fi

RADIUS_REST_AUTH_URL="${RADIUS_REST_AUTH_URL:-http://api:8000/auth}"

# 1) clients.conf: shared secret'i env'den al.
cat > /etc/freeradius/clients.conf <<EOF
client localhost {
  ipaddr = 127.0.0.1
  proto = *
  secret = ${RADIUS_SHARED_SECRET}
}

client docker_host {
  ipaddr = 172.18.0.1
  proto = *
  secret = ${RADIUS_SHARED_SECRET}
}
EOF

# 2) REST modülünü enable et (mods-enabled/rest).
cat > /etc/freeradius/mods-enabled/rest <<EOF
rest {
  connect_uri = "http://api:8000"

  authorize {
    uri = "${RADIUS_REST_AUTH_URL}"
    method = 'post'
    body = 'json'
    data = '{ "username": "%{User-Name}", "password": "%{User-Password}", "nas_ip_address": "%{%{NAS-IP-Address}:-}" }'
    timeout = 5.0
  }

  authenticate {
    uri = "${RADIUS_REST_AUTH_URL}"
    method = 'post'
    body = 'json'
    data = '{ "username": "%{User-Name}", "password": "%{User-Password}", "nas_ip_address": "%{%{NAS-IP-Address}:-}" }'
    timeout = 5.0
  }
}
EOF

# 3) sites-enabled/default patch.
#    Her start'ta sites-available/default'tan temiz kopya alıp minimal patch uyguluyoruz.
DEFAULT_SITE="/etc/freeradius/sites-enabled/default"
cp /etc/freeradius/sites-available/default "$DEFAULT_SITE"

echo "[nac] patching sites-enabled/default for REST auth..."

TMP_FILE="$(mktemp)"
awk '
  BEGIN { in_authorize=0; inserted=0 }
  /^authorize[ \t]*\{/ { in_authorize=1 }
  # authorize bloğu içinde "pap" satırından hemen önce REST doğrulama ekle.
  in_authorize && ($0 ~ /^[ \t]*pap[ \t]*$/) && (inserted==0) {
    print "\t\t# NAC_REST_PAP_AUTH: REST ile PAP doğrulama (API /auth)"
    print "\t\tif (User-Password && !control:Auth-Type) {"
    print "\t\t\trest"
    print "\t\t\tif (ok || updated) {"
    print "\t\t\t\tupdate control {"
    print "\t\t\t\t\t&Cleartext-Password := \"%{User-Password}\""
    print "\t\t\t\t\t&Auth-Type := PAP"
    print "\t\t\t\t}"
    print "\t\t\t\treturn"
    print "\t\t\t}"
    print "\t\t}"
    inserted=1
  }
  { print $0 }
' "$DEFAULT_SITE" > "$TMP_FILE"

mv "$TMP_FILE" "$DEFAULT_SITE"

echo "[nac] freeradius starting..."

if [ "$#" -gt 0 ]; then
  exec freeradius "$@"
fi

exec freeradius -f

