"""
Database layer for FedMed Pediatric FL Network.
Uses SQLite for persistent storage of hospitals, credentials, technicians, and cluster memberships.
"""
from __future__ import annotations

import json
import secrets
import sqlite3
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

DB_PATH = Path(__file__).resolve().parent / "data" / "pediatric_network.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _generate_hospital_id(name: str) -> str:
    """Generate a clean hospital ID like HOSP-APOLLO-9281"""
    words = re.findall(r"\b[A-Za-z]+", name)
    clean_prefix = words[0].upper()[:6] if words else "HOSP"
    if clean_prefix in ("HOSPIT", "THE", "CENTER"):
        clean_prefix = words[1].upper()[:6] if len(words) > 1 else "NODE"
    random_num = secrets.randbelow(9000) + 1000
    return f"HOSP-{clean_prefix}-{random_num}"


def _generate_access_key() -> str:
    """Generate a secure readable secret key like SEC-CHD-4A8F9B"""
    rand_hex = secrets.token_hex(4).upper()
    return f"SEC-CHD-{rand_hex}"


def _get_initials(name: str) -> str:
    words = [w for w in name.split() if w.lower() not in ("the", "of", "and", "hospital", "institute", "center")]
    if not words:
        words = name.split()
    if len(words) >= 2:
        return f"{words[0][0]}{words[1][0]}".upper()
    elif len(words) == 1 and len(words[0]) >= 2:
        return words[0][:2].upper()
    return "HP"


def init_db():
    """Create tables and seed initial records if empty."""
    conn = _get_connection()
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS admin_users (
                    email TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'admin',
                    created_at TEXT NOT NULL
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS hospitals (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    city TEXT NOT NULL,
                    country TEXT NOT NULL DEFAULT 'India',
                    contact_email TEXT NOT NULL,
                    access_key TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    authorized_modalities TEXT NOT NULL,
                    joined_clusters TEXT NOT NULL DEFAULT '[]',
                    contribution_score REAL DEFAULT 0.0,
                    patients_contributed INTEGER DEFAULT 0,
                    rounds_participated INTEGER DEFAULT 0,
                    initials TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    notes TEXT DEFAULT ''
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS technicians (
                    tech_id TEXT PRIMARY KEY,
                    hospital_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    pin TEXT NOT NULL DEFAULT '1234',
                    role_title TEXT DEFAULT 'Clinical Triage Tech',
                    status TEXT DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (hospital_id) REFERENCES hospitals (id) ON DELETE CASCADE
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS cluster_memberships (
                    hospital_id TEXT NOT NULL,
                    cluster_id TEXT NOT NULL,
                    dataset_path TEXT DEFAULT '',
                    joined_at TEXT NOT NULL,
                    PRIMARY KEY (hospital_id, cluster_id),
                    FOREIGN KEY (hospital_id) REFERENCES hospitals (id) ON DELETE CASCADE
                );
            """)

            # Seed Admin if not exists
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM admin_users")
            if cur.fetchone()[0] == 0:
                conn.execute("""
                    INSERT INTO admin_users (email, password, name, role, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    "admin@fedmed.network",
                    "admin123",
                    "Central Network Administrator",
                    "admin",
                    datetime.now(timezone.utc).isoformat()
                ))

            # Seed Hospitals if not exists
            cur.execute("SELECT COUNT(*) FROM hospitals")
            if cur.fetchone()[0] == 0:
                now_str = datetime.now(timezone.utc).isoformat()
                sample_hospitals = [
                    (
                        "HOSP-APOLLO-01",
                        "Apollo Children's Hospital",
                        "Chennai",
                        "India",
                        "cardiology@apollochildrens.in",
                        "APOLLO-CHD-2026",
                        "active",
                        json.dumps(["PCG", "ECG", "Echo"]),
                        json.dumps(["cluster-pcg", "cluster-ecg"]),
                        94.5,
                        1420,
                        48,
                        "AC",
                        now_str,
                        "Primary tertiary pediatric cardiac referral center with 12-lead ECG and digital phonocardiogram labs."
                    ),
                    (
                        "HOSP-AIIMS-02",
                        "AIIMS Pediatric Cardiology Center",
                        "New Delhi",
                        "India",
                        "research@aiims.edu.in",
                        "AIIMS-PED-8821",
                        "active",
                        json.dumps(["PCG", "ECG"]),
                        json.dumps(["cluster-pcg"]),
                        88.0,
                        980,
                        36,
                        "AI",
                        now_str,
                        "Autonomous apex institute focusing on congenital heart defect early auscultation screening."
                    ),
                    (
                        "HOSP-RAINBOW-03",
                        "Rainbow Children's Heart Institute",
                        "Hyderabad",
                        "India",
                        "pediatrics@rainbowhospitals.in",
                        "RAINBOW-CHD-4091",
                        "active",
                        json.dumps(["PCG", "Echo"]),
                        json.dumps(["cluster-echo"]),
                        76.2,
                        610,
                        24,
                        "RC",
                        now_str,
                        "Specialized neonatal critical care and echo video segmentation hub."
                    ),
                    (
                        "HOSP-FORTIS-04",
                        "Fortis Memorial Research Institute",
                        "Gurugram",
                        "India",
                        "fl-node@fortishealthcare.com",
                        "FORTIS-CHD-1092",
                        "pending",
                        json.dumps(["ECG", "Echo"]),
                        json.dumps([]),
                        0.0,
                        0,
                        0,
                        "FM",
                        now_str,
                        "Awaiting administrative onboarding and local IRB edge validation approval."
                    ),
                ]

                conn.executemany("""
                    INSERT INTO hospitals (
                        id, name, city, country, contact_email, access_key, status,
                        authorized_modalities, joined_clusters, contribution_score,
                        patients_contributed, rounds_participated, initials, created_at, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, sample_hospitals)

                # Seed cluster memberships
                conn.execute("""
                    INSERT INTO cluster_memberships (hospital_id, cluster_id, dataset_path, joined_at)
                    VALUES
                    ('HOSP-APOLLO-01', 'cluster-pcg', 'outputs/processed/pcg', ?),
                    ('HOSP-APOLLO-01', 'cluster-ecg', 'outputs/processed/ecg', ?),
                    ('HOSP-AIIMS-02', 'cluster-pcg', 'outputs/processed/pcg', ?),
                    ('HOSP-RAINBOW-03', 'cluster-echo', 'outputs/processed/echo', ?)
                """, (now_str, now_str, now_str, now_str))

                # Seed technicians
                conn.execute("""
                    INSERT INTO technicians (tech_id, hospital_id, name, pin, role_title, status, created_at)
                    VALUES
                    ('TECH-101', 'HOSP-APOLLO-01', 'Dr. Sarah Chen', '1234', 'Lead Clinical Triage Technician', 'active', ?),
                    ('TECH-102', 'HOSP-AIIMS-02', 'Rajesh Verma', '5678', 'Pediatric Sonographer & Edge Tech', 'active', ?),
                    ('TECH-103', 'HOSP-RAINBOW-03', 'Anita Sen', '4321', 'Auscultation Specialist', 'active', ?)
                """, (now_str, now_str, now_str))

    finally:
        conn.close()


def sync_fixed_dataset_hospitals():
    """Ensure hospitals have exact sample counts matching the real datasets in our repo."""
    conn = _get_connection()
    try:
        now_str = datetime.now(timezone.utc).isoformat()
        with conn:
            # Hospital A - CirCor DigiScope (PCG)
            conn.execute("""
                INSERT OR REPLACE INTO hospitals (
                    id, name, city, country, contact_email, access_key, status,
                    authorized_modalities, joined_clusters, contribution_score,
                    patients_contributed, rounds_participated, initials, created_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "HOSP-APOLLO-01",
                "Apollo Children's Hospital",
                "Chennai",
                "India",
                "cardiology@apollochildrens.in",
                "APOLLO-CHD-2026",
                "active",
                json.dumps(["PCG", "ECG", "Echo"]),
                json.dumps(["cluster-pcg"]),
                85.1,
                11162,
                37,
                "AC",
                now_str,
                "Lead site for CirCor DigiScope pediatric PCG dataset (11,162 acoustic segments: 8,822 normal, 2,340 murmur)."
            ))

            # Hospital B - ZZU-pECG (ECG)
            conn.execute("""
                INSERT OR REPLACE INTO hospitals (
                    id, name, city, country, contact_email, access_key, status,
                    authorized_modalities, joined_clusters, contribution_score,
                    patients_contributed, rounds_participated, initials, created_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "HOSP-AIIMS-02",
                "AIIMS Pediatric Cardiology Center",
                "New Delhi",
                "India",
                "research@aiims.edu.in",
                "AIIMS-PED-8821",
                "active",
                json.dumps(["ECG", "PCG"]),
                json.dumps(["cluster-ecg"]),
                88.2,
                14190,
                24,
                "AI",
                now_str,
                "Lead site for ZZU-pECG 12-lead pediatric ECG arrhythmia dataset (14,190 signals: 9,932 train, 2,127 val, 2,131 test)."
            ))

            # Hospital C - EchoNet-Pediatric (Echo)
            conn.execute("""
                INSERT OR REPLACE INTO hospitals (
                    id, name, city, country, contact_email, access_key, status,
                    authorized_modalities, joined_clusters, contribution_score,
                    patients_contributed, rounds_participated, initials, created_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "HOSP-RAINBOW-03",
                "Rainbow Children's Heart Institute",
                "Hyderabad",
                "India",
                "pediatrics@rainbowhospitals.in",
                "RAINBOW-CHD-4091",
                "active",
                json.dumps(["Echo", "PCG"]),
                json.dumps(["cluster-echo"]),
                89.2,
                3258,
                21,
                "RC",
                now_str,
                "Lead site for EchoNet-Pediatric video segmentation dataset (3,258 ED/ES pairs: 2,768 normal, 490 reduced EF)."
            ))

            # Hospital D - Fortis Memorial (Pending)
            conn.execute("""
                INSERT OR REPLACE INTO hospitals (
                    id, name, city, country, contact_email, access_key, status,
                    authorized_modalities, joined_clusters, contribution_score,
                    patients_contributed, rounds_participated, initials, created_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "HOSP-FORTIS-04",
                "Fortis Memorial Research Institute",
                "Gurugram",
                "India",
                "fl-node@fortishealthcare.com",
                "FORTIS-CHD-1092",
                "pending",
                json.dumps(["ECG", "Echo"]),
                json.dumps([]),
                0.0,
                0,
                0,
                "FM",
                now_str,
                "Awaiting central IRB verification and local federated container deployment."
            ))

            # Update cluster memberships matching datasets
            conn.execute("DELETE FROM cluster_memberships WHERE hospital_id IN ('HOSP-APOLLO-01', 'HOSP-AIIMS-02', 'HOSP-RAINBOW-03')")
            conn.execute("""
                INSERT INTO cluster_memberships (hospital_id, cluster_id, dataset_path, joined_at)
                VALUES
                ('HOSP-APOLLO-01', 'cluster-pcg', 'outputs/processed/pcg', ?),
                ('HOSP-AIIMS-02', 'cluster-ecg', 'outputs/processed/ecg', ?),
                ('HOSP-RAINBOW-03', 'cluster-echo', 'outputs/processed/echo', ?)
            """, (now_str, now_str, now_str))
    finally:
        conn.close()


# Ensure DB is created and fixed hospitals are synced
init_db()
sync_fixed_dataset_hospitals()


# ── Hospital Operations ────────────────────────────────────────────────────────

def list_hospitals() -> List[Dict[str, Any]]:
    """Return all registered hospitals."""
    conn = _get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM hospitals ORDER BY created_at DESC")
        rows = cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["authorized_modalities"] = json.loads(d["authorized_modalities"])
            d["joined_clusters"] = json.loads(d["joined_clusters"])
            result.append(d)
        return result
    finally:
        conn.close()


def get_hospital(hospital_id: str) -> Optional[Dict[str, Any]]:
    """Get single hospital by ID."""
    conn = _get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM hospitals WHERE id = ?", (hospital_id,))
        row = cur.fetchone()
        if not row:
            return None
        d = dict(row)
        d["authorized_modalities"] = json.loads(d["authorized_modalities"])
        d["joined_clusters"] = json.loads(d["joined_clusters"])
        return d
    finally:
        conn.close()


def create_hospital(
    name: str,
    city: str,
    country: str = "India",
    contact_email: str = "",
    authorized_modalities: Optional[List[str]] = None,
    notes: str = "",
    status: str = "active",
) -> Dict[str, Any]:
    """Admin creates a new hospital and generates secure credentials."""
    if authorized_modalities is None:
        authorized_modalities = ["PCG", "ECG", "Echo"]

    hospital_id = _generate_hospital_id(name)
    access_key = _generate_access_key()
    initials = _get_initials(name)
    now_str = datetime.now(timezone.utc).isoformat()

    conn = _get_connection()
    try:
        with conn:
            conn.execute("""
                INSERT INTO hospitals (
                    id, name, city, country, contact_email, access_key, status,
                    authorized_modalities, joined_clusters, contribution_score,
                    patients_contributed, rounds_participated, initials, created_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                hospital_id,
                name.strip(),
                city.strip(),
                country.strip(),
                contact_email.strip(),
                access_key,
                status,
                json.dumps(authorized_modalities),
                json.dumps([]),
                0.0,
                0,
                0,
                initials,
                now_str,
                notes.strip(),
            ))

            # Automatically create a default technician for this hospital
            tech_id = f"TECH-{secrets.randbelow(900) + 100}"
            conn.execute("""
                INSERT INTO technicians (tech_id, hospital_id, name, pin, role_title, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'active', ?)
            """, (
                tech_id,
                hospital_id,
                f"Triage Specialist ({initials})",
                "1234",
                "Clinical Triage Operator",
                now_str
            ))

        return get_hospital(hospital_id)
    finally:
        conn.close()


def update_hospital_status(hospital_id: str, status: str) -> Optional[Dict[str, Any]]:
    """Update status (active | suspended | pending)."""
    conn = _get_connection()
    try:
        with conn:
            conn.execute("UPDATE hospitals SET status = ? WHERE id = ?", (status, hospital_id))
        return get_hospital(hospital_id)
    finally:
        conn.close()


def regenerate_access_key(hospital_id: str) -> Optional[Dict[str, Any]]:
    """Regenerate secret access key for hospital."""
    new_key = _generate_access_key()
    conn = _get_connection()
    try:
        with conn:
            conn.execute("UPDATE hospitals SET access_key = ? WHERE id = ?", (new_key, hospital_id))
        return get_hospital(hospital_id)
    finally:
        conn.close()


def delete_hospital(hospital_id: str) -> bool:
    """Delete a hospital by ID."""
    conn = _get_connection()
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM cluster_memberships WHERE hospital_id = ?", (hospital_id,))
            cur.execute("DELETE FROM technicians WHERE hospital_id = ?", (hospital_id,))
            cur.execute("DELETE FROM hospitals WHERE id = ?", (hospital_id,))
            return cur.rowcount > 0
    finally:
        conn.close()


# ── Cluster Membership ────────────────────────────────────────────────────────

def join_cluster_db(hospital_id: str, cluster_id: str, dataset_path: str = "") -> bool:
    """Add hospital to cluster and update joined_clusters list."""
    hosp = get_hospital(hospital_id)
    if not hosp or hosp["status"] != "active":
        return False

    conn = _get_connection()
    try:
        with conn:
            now_str = datetime.now(timezone.utc).isoformat()
            conn.execute("""
                INSERT OR REPLACE INTO cluster_memberships (hospital_id, cluster_id, dataset_path, joined_at)
                VALUES (?, ?, ?, ?)
            """, (hospital_id, cluster_id, dataset_path, now_str))

            # Update JSON list in hospital table
            cur = conn.cursor()
            cur.execute("SELECT cluster_id FROM cluster_memberships WHERE hospital_id = ?", (hospital_id,))
            clusters = [r[0] for r in cur.fetchall()]
            conn.execute("UPDATE hospitals SET joined_clusters = ? WHERE id = ?", (json.dumps(clusters), hospital_id))
        return True
    finally:
        conn.close()


def leave_cluster_db(hospital_id: str, cluster_id: str) -> bool:
    """Remove hospital from cluster."""
    conn = _get_connection()
    try:
        with conn:
            conn.execute("""
                DELETE FROM cluster_memberships WHERE hospital_id = ? AND cluster_id = ?
            """, (hospital_id, cluster_id))

            cur = conn.cursor()
            cur.execute("SELECT cluster_id FROM cluster_memberships WHERE hospital_id = ?", (hospital_id,))
            clusters = [r[0] for r in cur.fetchall()]
            conn.execute("UPDATE hospitals SET joined_clusters = ? WHERE id = ?", (json.dumps(clusters), hospital_id))
        return True
    finally:
        conn.close()


def get_hospital_clusters(hospital_id: str) -> List[Dict[str, Any]]:
    """Return all clusters joined by hospital with dataset path and timestamp."""
    conn = _get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT cluster_id, dataset_path, joined_at
            FROM cluster_memberships
            WHERE hospital_id = ?
        """, (hospital_id,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def get_cluster_hospital_members(cluster_id: str) -> List[Dict[str, Any]]:
    """Return all hospitals currently participating in a given cluster."""
    conn = _get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT h.id, h.name, h.city, h.country, h.contribution_score, h.patients_contributed, cm.joined_at, cm.dataset_path
            FROM cluster_memberships cm
            JOIN hospitals h ON cm.hospital_id = h.id
            WHERE cm.cluster_id = ? AND h.status = 'active'
        """, (cluster_id,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# ── Technicians ───────────────────────────────────────────────────────────────

def list_technicians(hospital_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List lab technicians optionally filtered by hospital."""
    conn = _get_connection()
    try:
        cur = conn.cursor()
        if hospital_id:
            cur.execute("""
                SELECT t.*, h.name as hospital_name
                FROM technicians t
                JOIN hospitals h ON t.hospital_id = h.id
                WHERE t.hospital_id = ?
            """, (hospital_id,))
        else:
            cur.execute("""
                SELECT t.*, h.name as hospital_name
                FROM technicians t
                JOIN hospitals h ON t.hospital_id = h.id
            """)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# ── Authentication ────────────────────────────────────────────────────────────

def authenticate(
    role: str,
    hospital_id: Optional[str] = None,
    access_key: Optional[str] = None,
    email: Optional[str] = None,
    password: Optional[str] = None,
    tech_id: Optional[str] = None,
    pin: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Authenticate user by role:
    - 'admin': requires email & password
    - 'hospital': requires hospital_id & access_key (status must be active)
    - 'technician': requires hospital_id & pin, or tech_id & pin
    """
    conn = _get_connection()
    try:
        cur = conn.cursor()
        if role == "admin":
            cur.execute("SELECT * FROM admin_users WHERE email = ? AND password = ?", (email, password))
            admin = cur.fetchone()
            if admin:
                return {
                    "role": "admin",
                    "id": admin["email"],
                    "email": admin["email"],
                    "name": admin["name"],
                }
            return None

        elif role == "hospital":
            if not hospital_id or not access_key:
                return None
            cur.execute("SELECT * FROM hospitals WHERE id = ? AND access_key = ?", (hospital_id.strip(), access_key.strip()))
            hosp = cur.fetchone()
            if not hosp:
                return None
            hosp_dict = dict(hosp)
            if hosp_dict["status"] != "active":
                return {"error": "Hospital account is not active. Contact network administrator."}
            hosp_dict["authorized_modalities"] = json.loads(hosp_dict["authorized_modalities"])
            hosp_dict["joined_clusters"] = json.loads(hosp_dict["joined_clusters"])
            return {
                "role": "hospital",
                "id": hosp_dict["id"],
                "hospital_id": hosp_dict["id"],
                "name": hosp_dict["name"],
                "city": hosp_dict["city"],
                "hospital": hosp_dict,
            }

        elif role == "technician":
            if tech_id and pin:
                cur.execute("""
                    SELECT t.*, h.name as hospital_name, h.status as hospital_status
                    FROM technicians t
                    JOIN hospitals h ON t.hospital_id = h.id
                    WHERE t.tech_id = ? AND t.pin = ?
                """, (tech_id.strip(), pin.strip()))
            elif hospital_id and pin:
                cur.execute("""
                    SELECT t.*, h.name as hospital_name, h.status as hospital_status
                    FROM technicians t
                    JOIN hospitals h ON t.hospital_id = h.id
                    WHERE t.hospital_id = ? AND t.pin = ?
                """, (hospital_id.strip(), pin.strip()))
            else:
                return None

            tech = cur.fetchone()
            if not tech:
                return None
            tech_dict = dict(tech)
            if tech_dict["hospital_status"] != "active":
                return {"error": "Associated hospital is suspended or inactive."}
            return {
                "role": "technician",
                "id": tech_dict["tech_id"],
                "name": tech_dict["name"],
                "hospital_id": tech_dict["hospital_id"],
                "hospital_name": tech_dict["hospital_name"],
                "role_title": tech_dict["role_title"],
            }

        return None
    finally:
        conn.close()


# ── Global Network Stats for Admin ────────────────────────────────────────────

def get_network_metrics() -> Dict[str, Any]:
    """Summary of overall network statistics for the administrator."""
    conn = _get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM hospitals")
        total_hospitals = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM hospitals WHERE status = 'active'")
        active_hospitals = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM technicians")
        total_technicians = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM cluster_memberships")
        total_cluster_nodes = cur.fetchone()[0]

        cur.execute("SELECT SUM(patients_contributed), SUM(rounds_participated), AVG(contribution_score) FROM hospitals WHERE status = 'active'")
        sums = cur.fetchone()
        total_patients = sums[0] or 0
        total_rounds = sums[1] or 0
        avg_score = round(sums[2] or 0.0, 1)

        return {
            "total_hospitals": total_hospitals,
            "active_hospitals": active_hospitals,
            "total_technicians": total_technicians,
            "total_cluster_nodes": total_cluster_nodes,
            "total_patients_contributed": total_patients,
            "total_rounds_participated": total_rounds,
            "average_contribution_score": avg_score,
        }
    finally:
        conn.close()
