from src.auth.auth_manager import AuthManager

if __name__ == "__main__":
    a = AuthManager()
    print("Current Email Config:")
    for k, v in a.email_config.items():
        masked = v if "password" not in k else "*" * 10
        print(f"  {k}: {masked}")
