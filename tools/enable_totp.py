# Enable TOTP MFA for a user (demo helper)

from src.auth.auth_manager import AuthManager


def main():
    email = input("User email: ").strip()
    am = AuthManager()
    res = am.enable_totp(email)
    if res.get("error"):
        print("Error:", res["error"])
        return
    print("\nTOTP enabled.")
    print("Secret:", res["secret"])
    print("Provisioning URI:", res["provisioning_uri"])
    print("\nTip: paste the URI into a QR generator, or use an authenticator app that accepts URIs.")


if __name__ == "__main__":
    main()
