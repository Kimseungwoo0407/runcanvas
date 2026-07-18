from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta

from app.db.models import Base, InviteCode
from app.db.session import SessionLocal, engine
from app.repositories.users import UserRepository
from app.security import hash_password, hash_token, new_invite_code


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", required=True)
    args = parser.parse_args()
    if len(args.password) < 12:
        raise SystemExit("password must contain at least 12 characters")
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        repository = UserRepository(db)
        user = repository.get_by_username(args.username)
        if user is None:
            user = repository.create(args.username, hash_password(args.password), role="admin")
        else:
            user.password_hash = hash_password(args.password)
            user.role = "admin"
            user.is_active = True
        code = new_invite_code()
        invite = InviteCode(
            code_hash=hash_token(code),
            expires_at=datetime.now(UTC) + timedelta(days=30),
            max_uses=4,
            created_by=user.id,
        )
        db.add(invite)
        db.commit()
        print({"admin": user.username, "inviteCode": code, "expiresAt": invite.expires_at.isoformat()})


if __name__ == "__main__":
    main()
