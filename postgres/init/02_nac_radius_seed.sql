-- NAC seed data (local-dev örnekleri)
-- Not:
-- - Parolalar plaintext değildir: bcrypt (pgcrypto::crypt ile üretilmiş) hash olarak saklanır.
-- - FreeRADIUS tarafında password doğrulama yaklaşımının (rlm_pap/rlm_crypt) bu formatla uyumlu olması gerekir.

BEGIN;

-- ---- Grup tanımları (authorization için) ----
-- Bu isimleri FreeRADIUS SQL modülü/VLAN attribute map'lerinde referans edeceğiz.

-- Kullanıcı -> grup üyeliği
INSERT INTO radusergroup (username, groupname, priority) VALUES
  ('admin',    'admins',    0),
  ('employee', 'employees', 0),
  ('guest',    'guests',    0)
ON CONFLICT (username, groupname) DO NOTHING;

-- ---- PAP credential seed ----
-- attribute = 'Cleartext-Password' (FreeRADIUS SQL şemasında tipik)
-- op = ':=' (FreeRADIUS örnek şablonlarında sık görülür)
INSERT INTO radcheck (username, attribute, op, value) VALUES
  ('admin',    'Cleartext-Password', ':=', '$2a$06$Krq8bAJDBnO6JnOoLEPQQO7ZVAEyzCbAo6LaHGrKG5NunA28mtIPG'),
  ('employee', 'Cleartext-Password', ':=', '$2a$06$iGmUosKmS6.gnjA0s77PJOV2RRirJcZ6KN087Kjtdn0nO06cNdi1a'),
  ('guest',    'Cleartext-Password', ':=', '$2a$06$Rn/uRSa8onkNdOr8aM9H2eRdg.HnZZznQWA1gM.ccrnn42Xl0H3XW')
ON CONFLICT (username, attribute, op) DO NOTHING;

-- ---- Grup bazlı VLAN/policy mapping (radgroupreply) ----
-- Örnek VLAN attribute'ları (FreeRADIUS'ta yaygın):
-- - Tunnel-Medium-Type (IEEE-802)
-- - Tunnel-Private-Group-Id (VLAN ID)
-- - Policy-Name (opsiyonel, sisteminizde kullanılacak)
INSERT INTO radgroupreply (groupname, attribute, op, value) VALUES
  -- Admins -> VLAN 10
  ('admins',    'Tunnel-Medium-Type',      ':=', 'IEEE-802'),
  ('admins',    'Tunnel-Private-Group-Id',':=', '10'),
  ('admins',    'Policy-Name',            ':=', 'policy-admin'),

  -- Employees -> VLAN 20
  ('employees', 'Tunnel-Medium-Type',      ':=', 'IEEE-802'),
  ('employees', 'Tunnel-Private-Group-Id',':=', '20'),
  ('employees', 'Policy-Name',            ':=', 'policy-employee'),

  -- Guests -> VLAN 30
  ('guests',    'Tunnel-Medium-Type',      ':=', 'IEEE-802'),
  ('guests',    'Tunnel-Private-Group-Id',':=', '30'),
  ('guests',    'Policy-Name',            ':=', 'policy-guest')
ON CONFLICT (groupname, attribute, op) DO NOTHING;

COMMIT;

