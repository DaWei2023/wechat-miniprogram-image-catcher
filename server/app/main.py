"""授权服务器 FastAPI 应用."""

from __future__ import annotations

import os
import secrets
import sqlite3
import string
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DB_PATH = Path(os.environ.get("WXMP_LICENSE_DB", Path(__file__).resolve().parent.parent / "data" / "license.db"))
TRIAL_LIMIT = int(os.environ.get("WXMP_TRIAL_LIMIT", "10"))
ADMIN_TOKEN = os.environ.get("WXMP_ADMIN_TOKEN", "change-me-in-production")

app = FastAPI(title="WxMpCatcher License Server", version="1.0.0")


def _init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS activation_codes (
            code TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'unused',
            bound_device_id TEXT,
            license_token TEXT,
            activated_at TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS trial_devices (
            device_id TEXT PRIMARY KEY,
            images_used INTEGER NOT NULL DEFAULT 0,
            trial_exhausted INTEGER NOT NULL DEFAULT 0,
            first_seen TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )


@contextmanager
def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    _init_db(conn)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


class DeviceRequest(BaseModel):
    device_id: str = Field(min_length=16, max_length=128)


class TrialReportRequest(DeviceRequest):
    images_used: int = Field(ge=0)


class ActivateRequest(DeviceRequest):
    code: str = Field(min_length=8, max_length=64)
    app_version: str = ""


class ValidateRequest(DeviceRequest):
    license_token: str = Field(min_length=8, max_length=128)


class GenerateCodesRequest(BaseModel):
    count: int = Field(default=1, ge=1, le=500)
    prefix: str = "WXMP"


def _normalize_code(code: str) -> str:
    return code.strip().upper().replace(" ", "")


def _generate_code(prefix: str = "WXMP") -> str:
    alphabet = string.ascii_uppercase + string.digits
    parts = ["".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(3)]
    return f"{prefix}-{'-'.join(parts)}"


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _trial_payload(conn: sqlite3.Connection, device_id: str) -> dict:
    row = conn.execute(
        "SELECT images_used, trial_exhausted FROM trial_devices WHERE device_id = ?",
        (device_id,),
    ).fetchone()
    if not row:
        return {"images_used": 0, "trial_exhausted": False, "limit": TRIAL_LIMIT}
    return {
        "images_used": int(row["images_used"]),
        "trial_exhausted": bool(row["trial_exhausted"]),
        "limit": TRIAL_LIMIT,
    }


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/api/v1/trial/status")
def trial_status(body: DeviceRequest) -> dict:
    with get_db() as conn:
        payload = _trial_payload(conn, body.device_id)
        return {"ok": True, **payload}


@app.post("/api/v1/trial/report")
def trial_report(body: TrialReportRequest) -> dict:
    with get_db() as conn:
        now = _now()
        row = conn.execute(
            "SELECT images_used, trial_exhausted FROM trial_devices WHERE device_id = ?",
            (body.device_id,),
        ).fetchone()
        images_used = body.images_used
        exhausted = images_used >= TRIAL_LIMIT
        if row:
            images_used = max(int(row["images_used"]), body.images_used)
            exhausted = exhausted or bool(row["trial_exhausted"])
            conn.execute(
                """
                UPDATE trial_devices
                SET images_used = ?, trial_exhausted = ?, updated_at = ?
                WHERE device_id = ?
                """,
                (images_used, int(exhausted), now, body.device_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO trial_devices (device_id, images_used, trial_exhausted, first_seen, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (body.device_id, images_used, int(exhausted), now, now),
            )
        return {
            "ok": True,
            "images_used": images_used,
            "trial_exhausted": exhausted,
            "limit": TRIAL_LIMIT,
        }


@app.post("/api/v1/activate")
def activate(body: ActivateRequest) -> dict:
    code = _normalize_code(body.code)
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM activation_codes WHERE code = ?",
            (code,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="激活码不存在")

        if row["status"] == "revoked":
            raise HTTPException(status_code=403, detail="激活码已被禁用")

        if row["status"] == "used":
            if row["bound_device_id"] == body.device_id:
                return {
                    "message": "该设备已激活，授权已恢复",
                    "license_token": row["license_token"],
                }
            raise HTTPException(status_code=403, detail="激活码已在其它设备上使用")

        token = secrets.token_urlsafe(32)
        now = _now()
        conn.execute(
            """
            UPDATE activation_codes
            SET status = 'used', bound_device_id = ?, license_token = ?, activated_at = ?
            WHERE code = ?
            """,
            (body.device_id, token, now, code),
        )
        return {"message": "激活成功", "license_token": token}


@app.post("/api/v1/validate")
def validate(body: ValidateRequest) -> dict:
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT * FROM activation_codes
            WHERE license_token = ? AND bound_device_id = ? AND status = 'used'
            """,
            (body.license_token, body.device_id),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=403, detail="授权无效或已失效")
        return {"valid": True}


@app.post("/admin/generate-codes")
def generate_codes(body: GenerateCodesRequest, admin_token: str) -> dict:
    if admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="管理员令牌无效")
    codes: list[str] = []
    now = _now()
    with get_db() as conn:
        for _ in range(body.count):
            for _attempt in range(20):
                code = _generate_code(body.prefix)
                exists = conn.execute(
                    "SELECT 1 FROM activation_codes WHERE code = ?",
                    (code,),
                ).fetchone()
                if not exists:
                    conn.execute(
                        "INSERT INTO activation_codes (code, status, created_at) VALUES (?, 'unused', ?)",
                        (code, now),
                    )
                    codes.append(code)
                    break
    return {"count": len(codes), "codes": codes}
