-- NAC FreeRADIUS SQL şeması (local-dev için)
-- Not:
-- - FreeRADIUS `rlm_sql` tarafında standart tablo/kolon isimlerini takip eder.
-- - Bu dosya PostgreSQL ilk başlatma anında `/docker-entrypoint-initdb.d/` üzerinden çalıştırılır.

BEGIN;

-- PAP credential'ları (kullanıcı bazlı) için
CREATE TABLE IF NOT EXISTS radcheck (
  username  VARCHAR(64)  NOT NULL,
  attribute VARCHAR(64)  NOT NULL,
  op        VARCHAR(2)   NOT NULL,
  value     VARCHAR(253) NOT NULL,
  PRIMARY KEY (username, attribute, op)
);

-- Kullanıcı bazlı reply/override'lar için
CREATE TABLE IF NOT EXISTS radreply (
  username  VARCHAR(64)  NOT NULL,
  attribute VARCHAR(64)  NOT NULL,
  op        VARCHAR(2)   NOT NULL,
  value     VARCHAR(253) NOT NULL,
  PRIMARY KEY (username, attribute, op)
);

-- Kullanıcı -> grup üyeliği (authorization için)
CREATE TABLE IF NOT EXISTS radusergroup (
  username  VARCHAR(64) NOT NULL,
  groupname VARCHAR(64) NOT NULL,
  priority  INTEGER      NOT NULL DEFAULT 0,
  PRIMARY KEY (username, groupname)
);

-- Grup bazlı reply'lar (VLAN/policy dönüşleri için)
CREATE TABLE IF NOT EXISTS radgroupreply (
  groupname VARCHAR(64)  NOT NULL,
  attribute VARCHAR(64)  NOT NULL,
  op        VARCHAR(2)   NOT NULL,
  value     VARCHAR(253) NOT NULL,
  PRIMARY KEY (groupname, attribute, op)
);

-- Accounting kayıtları (session başlat/bitir, octets, süre vs.)
CREATE TABLE IF NOT EXISTS radacct (
  acctsessionid      VARCHAR(64)  NOT NULL,
  acctuniqueid       VARCHAR(64)  NOT NULL PRIMARY KEY,
  username           VARCHAR(64),
  groupname          VARCHAR(64),
  realm              VARCHAR(64),
  nasipaddress       INET,
  nasportid          VARCHAR(32),
  nasporttype        INTEGER,

  connectinfo_start  TEXT,
  acctstarttime      TIMESTAMPTZ  NOT NULL DEFAULT now(),
  acctupdatetime     TIMESTAMPTZ,
  acctinterval       INTEGER,

  acctstoptime       TIMESTAMPTZ,
  acctsessiontime    INTEGER,
  terminated          VARCHAR(64),
  cause               VARCHAR(64),
  inputoctets        BIGINT,
  outputoctets       BIGINT,

  -- Flex: FreeRADIUS'ın farklı modüllerinden gelen ek alanlar için.
  -- Şimdilik şemayı sade tuttuk; ileride gerekirse genişletiriz.
  eventtimestamp     TIMESTAMPTZ
);

-- ---- Index önerileri (performans) ----
-- Auth look-up: username + attribute ile hızlı sorgu
CREATE INDEX IF NOT EXISTS idx_radcheck_username_attribute
  ON radcheck (username, attribute);

CREATE INDEX IF NOT EXISTS idx_radreply_username_attribute
  ON radreply (username, attribute);

-- Group mapping look-up
CREATE INDEX IF NOT EXISTS idx_radusergroup_groupname
  ON radusergroup (groupname);

-- Authorization response look-up
CREATE INDEX IF NOT EXISTS idx_radgroupreply_groupname_attribute
  ON radgroupreply (groupname, attribute);

-- Accounting query'leri: kullanıcı, NAS IP, başlangıç zamanı ile filtreleme
CREATE INDEX IF NOT EXISTS idx_radacct_username
  ON radacct (username);

CREATE INDEX IF NOT EXISTS idx_radacct_nasipaddress
  ON radacct (nasipaddress);

CREATE INDEX IF NOT EXISTS idx_radacct_acctstarttime
  ON radacct (acctstarttime);

COMMIT;

